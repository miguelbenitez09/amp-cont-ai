// Package main implements the High-Performance API Gateway for Panama PortOps-AI / amp-cont-ai.
// Author: Ing. Miguel Antonio Benítez González (Universidad Tecnológica de Panamá - UTP)
// License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
// Version: v2.0.0

package main

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"
)

// Platform metadata constants.
const (
	PlatformName    = "amp-cont-ai"
	PlatformVersion = "v2.0.0"
	PlatformAuthor  = "Ing. Miguel Antonio Benítez González (UTP)"
	PlatformLicense = "GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution"
	DefaultPort     = "8000"
	DefaultUpstream = "http://127.0.0.1:8001"
	DefaultStatic   = "src/serving/static"
)

var browserSecurityHeaders = map[string]string{
	"X-Content-Type-Options":       "nosniff",
	"X-Frame-Options":              "DENY",
	"Referrer-Policy":              "strict-origin-when-cross-origin",
	"Permissions-Policy":           "camera=(), microphone=(), geolocation=(), payment=(), usb=(), fullscreen=(self)",
	"Cross-Origin-Opener-Policy":   "same-origin",
	"Cross-Origin-Resource-Policy": "same-origin",
	"Content-Security-Policy":      "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; img-src 'self' data:; font-src 'self' https://cdn.jsdelivr.net data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
}

// Metrics counters.
type Metrics struct {
	TotalRequests  uint64
	ProxyRequests  uint64
	StaticRequests uint64
	FailedRequests uint64
	ActiveClients  int64
	StartTime      time.Time
}

var globalMetrics = &Metrics{
	StartTime: time.Now(),
}

// TokenBucketRateLimiter implements a lightweight in-memory rate limiter per IP.
type clientLimiter struct {
	tokens     float64
	lastUpdate time.Time
}

type RateLimiter struct {
	mu      sync.Mutex
	clients map[string]*clientLimiter
	rate    float64 // tokens per second
	burst   float64 // maximum tokens
}

func NewRateLimiter(rate, burst float64) *RateLimiter {
	rl := &RateLimiter{
		clients: make(map[string]*clientLimiter),
		rate:    rate,
		burst:   burst,
	}
	// Background cleanup of stale IP records every 5 minutes.
	go func() {
		for {
			time.Sleep(5 * time.Minute)
			rl.cleanup()
		}
	}()
	return rl
}

func (rl *RateLimiter) cleanup() {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	cutoff := time.Now().Add(-10 * time.Minute)
	for ip, c := range rl.clients {
		if c.lastUpdate.Before(cutoff) {
			delete(rl.clients, ip)
		}
	}
}

func (rl *RateLimiter) Allow(ip string) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	c, exists := rl.clients[ip]
	if !exists {
		rl.clients[ip] = &clientLimiter{
			tokens:     rl.burst - 1,
			lastUpdate: now,
		}
		return true
	}

	elapsed := now.Sub(c.lastUpdate).Seconds()
	c.lastUpdate = now
	c.tokens += elapsed * rl.rate
	if c.tokens > rl.burst {
		c.tokens = rl.burst
	}

	if c.tokens >= 1.0 {
		c.tokens -= 1.0
		return true
	}
	return false
}

// GatewayServer holds the state for routing, static serving, and proxying.
type GatewayServer struct {
	port        string
	upstreamURL *url.URL
	proxy       *httputil.ReverseProxy
	staticDir   string
	rateLimiter *RateLimiter
	httpClient  *http.Client
}

func generateRequestID() string {
	b := make([]byte, 16)
	_, err := rand.Read(b)
	if err != nil {
		return fmt.Sprintf("%d", time.Now().UnixNano())
	}
	return hex.EncodeToString(b)
}

func getClientIP(r *http.Request) string {
	ip := r.RemoteAddr
	if colon := strings.LastIndex(ip, ":"); colon != -1 {
		ip = ip[:colon]
	}
	rawIP := strings.Trim(ip, "[]")

	// Only trust forwarded proxy headers if the remote connection comes from loopback or private network
	if rawIP == "127.0.0.1" || rawIP == "::1" || strings.HasPrefix(rawIP, "10.") || strings.HasPrefix(rawIP, "192.168.") {
		xRealIP := r.Header.Get("X-Real-IP")
		if xRealIP != "" {
			return strings.TrimSpace(xRealIP)
		}
		xff := r.Header.Get("X-Forwarded-For")
		if xff != "" {
			parts := strings.Split(xff, ",")
			return strings.TrimSpace(parts[0])
		}
	}
	return rawIP
}

func NewGatewayServer(port, upstreamStr, staticDir string) (*GatewayServer, error) {
	parsedUpstream, err := url.Parse(upstreamStr)
	if err != nil {
		return nil, fmt.Errorf("invalid upstream URL: %w", err)
	}

	proxy := httputil.NewSingleHostReverseProxy(parsedUpstream)
	proxy.Transport = &http.Transport{
		Proxy:                 http.ProxyFromEnvironment,
		MaxIdleConns:          1000,
		MaxIdleConnsPerHost:   200,
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:   10 * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
	}
	originalDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		originalHost := req.Host
		originalDirector(req)
		req.Host = parsedUpstream.Host
		if req.Header.Get("X-Request-ID") == "" {
			req.Header.Set("X-Request-ID", generateRequestID())
		}
		req.Header.Set("X-Forwarded-Host", originalHost)
		proto := "http"
		if req.TLS != nil {
			proto = "https"
		}
		req.Header.Set("X-Forwarded-Proto", proto)
		req.Header.Set("X-Gateway-Engine", "Go-PortOps-v2.0")
	}
	proxy.ModifyResponse = func(response *http.Response) error {
		// The edge owns browser policy; discard permissive upstream CORS and duplicates.
		for name := range response.Header {
			if strings.HasPrefix(strings.ToLower(name), "access-control-") {
				response.Header.Del(name)
			}
		}
		for name := range browserSecurityHeaders {
			response.Header.Del(name)
		}
		return nil
	}

	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, proxyErr error) {
		atomic.AddUint64(&globalMetrics.FailedRequests, 1)
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.WriteHeader(http.StatusServiceUnavailable)
		_ = json.NewEncoder(w).Encode(map[string]any{
			"status":      "upstream_unavailable",
			"error":       "Python FastAPI backend engine is starting or currently unreachable.",
			"detail":      proxyErr.Error(),
			"retry_after": 3,
			"platform":    PlatformName,
			"version":     PlatformVersion,
		})
	}

	return &GatewayServer{
		port:        port,
		upstreamURL: parsedUpstream,
		proxy:       proxy,
		staticDir:   staticDir,
		rateLimiter: NewRateLimiter(100.0, 200.0),
		httpClient: &http.Client{
			Timeout: 4 * time.Second,
		},
	}, nil
}

// Middleware: Security Headers and CORS.
func (s *GatewayServer) securityHeadersMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Content-Type-Options", "nosniff")
		for name, value := range browserSecurityHeaders {
			w.Header().Set(name, value)
		}
		w.Header().Set("X-XSS-Protection", "1; mode=block")
		w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
		w.Header().Set("Server", "amp-cont-ai-gateway/2.0 (Go 1.26)")
		w.Header().Set("X-Platform-Author", PlatformAuthor)
		w.Header().Set("X-Platform-License", PlatformLicense)

		// CORS is denied by default. Additional origins must be explicitly configured.
		origin := r.Header.Get("Origin")
		if origin != "" {
			scheme := "http"
			if r.TLS != nil {
				scheme = "https"
			}
			isAllowed := validOrigin(origin) && origin == scheme+"://"+r.Host
			for _, configured := range strings.Split(os.Getenv("PORTOPS_CORS_ORIGINS"), ",") {
				if validOrigin(origin) && origin == strings.TrimSpace(configured) {
					isAllowed = true
				}
			}
			w.Header().Add("Vary", "Origin")
			if isAllowed {
				w.Header().Set("Access-Control-Allow-Origin", origin)
				w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
				w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, X-Request-ID, X-CSRF-Token")
				w.Header().Set("Access-Control-Allow-Credentials", "true")
			}
			if r.Method == http.MethodOptions {
				if !isAllowed {
					http.Error(w, "Origin not allowed", http.StatusForbidden)
					return
				}
				w.WriteHeader(http.StatusNoContent)
				return
			}
		}

		next.ServeHTTP(w, r)
	})
}

func validOrigin(origin string) bool {
	parsed, err := url.Parse(origin)
	return err == nil && (parsed.Scheme == "http" || parsed.Scheme == "https") && parsed.Hostname() != "" && parsed.User == nil && parsed.Path == "" && parsed.RawQuery == "" && parsed.Fragment == ""
}

// Middleware: Rate Limiter.
func (s *GatewayServer) rateLimitMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Bypass rate limiting for local health checks
		if strings.HasPrefix(r.URL.Path, "/health/") {
			next.ServeHTTP(w, r)
			return
		}

		clientIP := getClientIP(r)
		if !s.rateLimiter.Allow(clientIP) {
			atomic.AddUint64(&globalMetrics.FailedRequests, 1)
			w.Header().Set("Content-Type", "application/json")
			w.Header().Set("Retry-After", "1")
			w.WriteHeader(http.StatusTooManyRequests)
			_ = json.NewEncoder(w).Encode(map[string]string{
				"error":  "Rate limit exceeded. Too many requests.",
				"hint":   "Limit is 100 requests/sec with burst of 200.",
				"client": clientIP,
			})
			return
		}
		next.ServeHTTP(w, r)
	})
}

// Native Health Endpoints.
func (s *GatewayServer) handleHealthLive(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]any{
		"status":    "alive",
		"engine":    "go-gateway-v2.0",
		"gateway":   "operational",
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"uptime_s":  time.Since(globalMetrics.StartTime).Seconds(),
		"author":    PlatformAuthor,
	})
}

func (s *GatewayServer) handleHealthReady(w http.ResponseWriter, r *http.Request) {
	// Probe upstream FastAPI readiness
	upstreamResp, err := s.httpClient.Get(s.upstreamURL.String() + "/health/ready")
	upstreamReady := false
	var upstreamDetails any = nil

	if err == nil {
		defer upstreamResp.Body.Close()
		if upstreamResp.StatusCode == http.StatusOK {
			upstreamReady = true
			var bodyMap map[string]any
			if decodeErr := json.NewDecoder(upstreamResp.Body).Decode(&bodyMap); decodeErr == nil {
				upstreamDetails = bodyMap
			}
		}
	}

	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	if !upstreamReady {
		w.WriteHeader(http.StatusServiceUnavailable)
		_ = json.NewEncoder(w).Encode(map[string]any{
			"status":   "warming_up",
			"gateway":  "ready",
			"upstream": "connecting",
			"target":   s.upstreamURL.String(),
			"hint":     "FastAPI ML microservice is initializing models and lakehouse caches.",
		})
		return
	}

	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]any{
		"status":   "ready",
		"gateway":  "ready",
		"upstream": "ready",
		"details":  upstreamDetails,
	})
}

func (s *GatewayServer) handleHealthVersion(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]any{
		"platform": PlatformName,
		"version":  PlatformVersion,
		"release":  "Panama MLOps PortOps Engine",
		"author":   PlatformAuthor,
		"license":  PlatformLicense,
		"go_ver":   runtime.Version(),
		"arch":     runtime.GOARCH,
		"os":       runtime.GOOS,
	})
}

func (s *GatewayServer) handleGatewayStatus(w http.ResponseWriter, r *http.Request) {
	var mem runtime.MemStats
	runtime.ReadMemStats(&mem)

	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]any{
		"engine":          "Go High-Performance API Gateway",
		"version":         PlatformVersion,
		"uptime_seconds":  time.Since(globalMetrics.StartTime).Seconds(),
		"total_requests":  atomic.LoadUint64(&globalMetrics.TotalRequests),
		"proxy_requests":  atomic.LoadUint64(&globalMetrics.ProxyRequests),
		"static_requests": atomic.LoadUint64(&globalMetrics.StaticRequests),
		"failed_requests": atomic.LoadUint64(&globalMetrics.FailedRequests),
		"goroutines":      runtime.NumGoroutine(),
		"memory_alloc_mb": float64(mem.Alloc) / (1024 * 1024),
		"sys_mem_mb":      float64(mem.Sys) / (1024 * 1024),
		"gc_cycles":       mem.NumGC,
	})
}

func (s *GatewayServer) handlePrometheusMetrics(w http.ResponseWriter, r *http.Request) {
	var mem runtime.MemStats
	runtime.ReadMemStats(&mem)

	w.Header().Set("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
	uptime := time.Since(globalMetrics.StartTime).Seconds()

	metricsText := fmt.Sprintf(`# HELP portops_gateway_requests_total Total requests processed by the Go API gateway.
# TYPE portops_gateway_requests_total counter
portops_gateway_requests_total{type="total"} %d
portops_gateway_requests_total{type="proxy"} %d
portops_gateway_requests_total{type="static"} %d
portops_gateway_requests_total{type="failed"} %d

# HELP portops_gateway_uptime_seconds Total running seconds of the gateway process.
# TYPE portops_gateway_uptime_seconds gauge
portops_gateway_uptime_seconds %.2f

# HELP portops_gateway_goroutines Current active goroutines count.
# TYPE portops_gateway_goroutines gauge
portops_gateway_goroutines %d

# HELP portops_gateway_memory_bytes Gateway allocated heap memory in bytes.
# TYPE portops_gateway_memory_bytes gauge
portops_gateway_memory_bytes %d
`,
		atomic.LoadUint64(&globalMetrics.TotalRequests),
		atomic.LoadUint64(&globalMetrics.ProxyRequests),
		atomic.LoadUint64(&globalMetrics.StaticRequests),
		atomic.LoadUint64(&globalMetrics.FailedRequests),
		uptime,
		runtime.NumGoroutine(),
		mem.Alloc,
	)

	_, _ = io.WriteString(w, metricsText)
}

// Master Handler.
func (s *GatewayServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	atomic.AddUint64(&globalMetrics.TotalRequests, 1)

	path := r.URL.Path

	// 1. Native Go endpoints
	switch path {
	case "/health/gateway":
		s.handleHealthLive(w, r)
		return
	case "/health/gateway/version":
		s.handleHealthVersion(w, r)
		return
	case "/metrics":
		s.handlePrometheusMetrics(w, r)
		return
	case "/api/v1/gateway/status":
		s.handleGatewayStatus(w, r)
		return
	}

	// 2. Proxy API, Health, Model, Prediction, and Simulation routes to Python FastAPI backend
	if strings.HasPrefix(path, "/api/") ||
		strings.HasPrefix(path, "/health") ||
		strings.HasPrefix(path, "/predict") ||
		strings.HasPrefix(path, "/simulate") ||
		strings.HasPrefix(path, "/model/") ||
		strings.HasPrefix(path, "/docs") ||
		strings.HasPrefix(path, "/openapi.json") ||
		strings.HasPrefix(path, "/redoc") {
		atomic.AddUint64(&globalMetrics.ProxyRequests, 1)
		s.proxy.ServeHTTP(w, r)
		return
	}

	// 3. Static files serving with cache headers
	atomic.AddUint64(&globalMetrics.StaticRequests, 1)

	// Clean path
	relPath := strings.TrimPrefix(path, "/")
	if relPath == "" || relPath == "landing.html" {
		landingFile := filepath.Join(s.staticDir, "landing.html")
		if _, err := os.Stat(landingFile); err == nil {
			w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
			w.Header().Set("Content-Type", "text/html; charset=utf-8")
			http.ServeFile(w, r, landingFile)
			return
		}
		w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		http.ServeFile(w, r, filepath.Join(s.staticDir, "index.html"))
		return
	}

	if relPath == "app" || relPath == "app/" || relPath == "index.html" {
		w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		http.ServeFile(w, r, filepath.Join(s.staticDir, "index.html"))
		return
	}

	// Support both /static/* and /* URL paths
	cleanSubPath := strings.TrimPrefix(relPath, "static/")
	targetPath := filepath.Join(s.staticDir, filepath.FromSlash(cleanSubPath))
	fileInfo, err := os.Stat(targetPath)
	if err == nil && fileInfo.IsDir() {
		targetPath = filepath.Join(targetPath, "index.html")
		fileInfo, err = os.Stat(targetPath)
	}
	if err != nil || fileInfo.IsDir() {
		// Also check directly without trimming
		targetPath = filepath.Join(s.staticDir, filepath.FromSlash(relPath))
		fileInfo, err = os.Stat(targetPath)
	}

	if err == nil && !fileInfo.IsDir() {
		// Set explicit MIME types for web assets to prevent strict MIME errors
		switch {
		case strings.HasSuffix(targetPath, ".css"):
			w.Header().Set("Content-Type", "text/css; charset=utf-8")
		case strings.HasSuffix(targetPath, ".js"):
			w.Header().Set("Content-Type", "application/javascript; charset=utf-8")
		case strings.HasSuffix(targetPath, ".svg"):
			w.Header().Set("Content-Type", "image/svg+xml")
		case strings.HasSuffix(targetPath, ".png"):
			w.Header().Set("Content-Type", "image/png")
		case strings.HasSuffix(targetPath, ".ico"):
			w.Header().Set("Content-Type", "image/x-icon")
		case strings.HasSuffix(targetPath, ".json"):
			w.Header().Set("Content-Type", "application/json; charset=utf-8")
		}

		// Static assets: disable aggressive caching during development and updates so user browser always gets latest code
		if strings.HasSuffix(targetPath, ".css") || strings.HasSuffix(targetPath, ".js") {
			w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
			w.Header().Set("Pragma", "no-cache")
			w.Header().Set("Expires", "0")
		} else if strings.HasSuffix(targetPath, ".png") || strings.HasSuffix(targetPath, ".svg") || strings.HasSuffix(targetPath, ".ico") {
			w.Header().Set("Cache-Control", "public, max-age=3600")
		}
		file, openErr := os.Open(targetPath)
		if openErr != nil {
			http.NotFound(w, r)
			return
		}
		defer file.Close()
		http.ServeContent(w, r, fileInfo.Name(), fileInfo.ModTime(), file)
		return
	}

	// If a resource file (.css, .js, .png, etc.) was not found, return 404 instead of index.html
	if strings.Contains(relPath, ".") && !strings.HasSuffix(relPath, ".html") {
		http.NotFound(w, r)
		return
	}

	// 4. Single-Page Application (SPA) fallback to index.html for HTML / document routes
	w.Header().Set("Cache-Control", "no-cache, no-store, must-revalidate")
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	http.ServeFile(w, r, filepath.Join(s.staticDir, "index.html"))
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = os.Getenv("AMP_PORT")
		if port == "" {
			port = DefaultPort
		}
	}

	upstream := os.Getenv("UPSTREAM_URL")
	if upstream == "" {
		upstream = DefaultUpstream
	}

	staticDir := os.Getenv("STATIC_DIR")
	if staticDir == "" {
		staticDir = DefaultStatic
	}

	// Resolve absolute path for static directory if needed
	if !filepath.IsAbs(staticDir) {
		cwd, err := os.Getwd()
		if err == nil {
			target := filepath.Join(cwd, staticDir)
			if _, statErr := os.Stat(target); statErr == nil {
				staticDir = target
			}
		}
	}

	server, err := NewGatewayServer(port, upstream, staticDir)
	if err != nil {
		log.Fatalf("[FATAL] Failed to initialize Go Gateway: %v", err)
	}

	handler := server.securityHeadersMiddleware(server.rateLimitMiddleware(server))

	httpServer := &http.Server{
		Addr:         ":" + port,
		Handler:      handler,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 60 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	log.Printf("================================================================================")
	log.Printf(" Panama PortOps-AI High-Performance API Gateway (Go Engine v2.0)")
	log.Printf(" Author: %s", PlatformAuthor)
	log.Printf(" License: %s", PlatformLicense)
	log.Printf(" Listening on port: :%s", port)
	log.Printf(" Reverse Proxy target -> %s", upstream)
	log.Printf(" Static Assets directory -> %s", staticDir)
	log.Printf("================================================================================")

	// Graceful shutdown handling
	stopChan := make(chan os.Signal, 1)
	signal.Notify(stopChan, os.Interrupt, syscall.SIGTERM)

	go func() {
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[FATAL] HTTP server failure: %v", err)
		}
	}()

	<-stopChan
	log.Println("[INFO] Shutting down gateway gracefully...")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := httpServer.Shutdown(ctx); err != nil {
		log.Printf("[ERROR] Gateway shutdown error: %v", err)
	}
	log.Println("[INFO] Gateway stopped cleanly.")
}
