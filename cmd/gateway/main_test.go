// Tests for High-Performance API Gateway
// Author: Ing. Miguel Antonio Benítez González (UTP) - GNU GPL-3.0

package main

import (
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func setupTestEnvironment(t *testing.T) (string, func()) {
	t.Helper()
	tempDir, err := os.MkdirTemp("", "gateway_test_*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}

	indexContent := "<html><body><h1>Panama PortOps-AI Test Portal</h1></body></html>"
	err = os.WriteFile(filepath.Join(tempDir, "index.html"), []byte(indexContent), 0644)
	if err != nil {
		t.Fatalf("Failed to write test index.html: %v", err)
	}

	cleanup := func() {
		os.RemoveAll(tempDir)
	}
	return tempDir, cleanup
}

func TestHealthLive(t *testing.T) {
	staticDir, cleanup := setupTestEnvironment(t)
	defer cleanup()

	server, err := NewGatewayServer("8000", "http://127.0.0.1:8001", staticDir)
	if err != nil {
		t.Fatalf("NewGatewayServer failed: %v", err)
	}

	handler := server.securityHeadersMiddleware(server)
	req := httptest.NewRequest(http.MethodGet, "/health/gateway", nil)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rr.Code)
	}

	var body map[string]any
	if err := json.Unmarshal(rr.Body.Bytes(), &body); err != nil {
		t.Fatalf("Failed to parse response: %v", err)
	}

	if body["status"] != "alive" {
		t.Errorf("Expected status 'alive', got %v", body["status"])
	}
	if body["engine"] != "go-gateway-v2.0" {
		t.Errorf("Expected engine 'go-gateway-v2.0', got %v", body["engine"])
	}
}

func TestHealthVersion(t *testing.T) {
	staticDir, cleanup := setupTestEnvironment(t)
	defer cleanup()

	server, err := NewGatewayServer("8000", "http://127.0.0.1:8001", staticDir)
	if err != nil {
		t.Fatalf("NewGatewayServer failed: %v", err)
	}

	handler := server.securityHeadersMiddleware(server)
	req := httptest.NewRequest(http.MethodGet, "/health/gateway/version", nil)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rr.Code)
	}

	var body map[string]any
	if err := json.Unmarshal(rr.Body.Bytes(), &body); err != nil {
		t.Fatalf("Failed to parse response: %v", err)
	}

	if body["platform"] != PlatformName {
		t.Errorf("Expected platform %s, got %v", PlatformName, body["platform"])
	}
	if body["version"] != PlatformVersion {
		t.Errorf("Expected version %s, got %v", PlatformVersion, body["version"])
	}
}

func TestPrometheusMetrics(t *testing.T) {
	staticDir, cleanup := setupTestEnvironment(t)
	defer cleanup()

	server, err := NewGatewayServer("8000", "http://127.0.0.1:8001", staticDir)
	if err != nil {
		t.Fatalf("NewGatewayServer failed: %v", err)
	}

	handler := server.securityHeadersMiddleware(server)
	req := httptest.NewRequest(http.MethodGet, "/metrics", nil)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", rr.Code)
	}

	body := rr.Body.String()
	if !strings.Contains(body, "portops_gateway_requests_total") {
		t.Errorf("Metrics output missing 'portops_gateway_requests_total'")
	}
	if !strings.Contains(body, "portops_gateway_uptime_seconds") {
		t.Errorf("Metrics output missing 'portops_gateway_uptime_seconds'")
	}
}

func TestSecurityHeaders(t *testing.T) {
	staticDir, cleanup := setupTestEnvironment(t)
	defer cleanup()

	server, err := NewGatewayServer("8000", "http://127.0.0.1:8001", staticDir)
	if err != nil {
		t.Fatalf("NewGatewayServer failed: %v", err)
	}

	handler := server.securityHeadersMiddleware(server)
	req := httptest.NewRequest(http.MethodGet, "/health/live", nil)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Header().Get("X-Content-Type-Options") != "nosniff" {
		t.Errorf("Missing or invalid X-Content-Type-Options header")
	}
	if rr.Header().Get("X-Frame-Options") != "DENY" {
		t.Errorf("Missing or invalid X-Frame-Options header")
	}
	if rr.Header().Get("X-Platform-Author") != PlatformAuthor {
		t.Errorf("Missing or invalid X-Platform-Author header")
	}
}

func TestReverseProxyToMockFastAPI(t *testing.T) {
	staticDir, cleanup := setupTestEnvironment(t)
	defer cleanup()

	// Mock FastAPI upstream server
	mockFastAPI := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/api/v1/mock-test" {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			_, _ = io.WriteString(w, `{"success": true, "routed_to": "fastapi"}`)
			return
		}
		http.NotFound(w, r)
	}))
	defer mockFastAPI.Close()

	server, err := NewGatewayServer("8000", mockFastAPI.URL, staticDir)
	if err != nil {
		t.Fatalf("NewGatewayServer failed: %v", err)
	}

	handler := server.securityHeadersMiddleware(server)
	req := httptest.NewRequest(http.MethodGet, "/api/v1/mock-test", nil)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if rr.Code != http.StatusOK {
		t.Errorf("Expected status 200 from upstream, got %d", rr.Code)
	}

	var body map[string]any
	if err := json.Unmarshal(rr.Body.Bytes(), &body); err != nil {
		t.Fatalf("Failed to parse upstream response: %v", err)
	}

	if body["routed_to"] != "fastapi" {
		t.Errorf("Expected routed_to 'fastapi', got %v", body["routed_to"])
	}
}

func TestStaticServingAndSPAFallback(t *testing.T) {
	staticDir, cleanup := setupTestEnvironment(t)
	defer cleanup()

	server, err := NewGatewayServer("8000", "http://127.0.0.1:8001", staticDir)
	if err != nil {
		t.Fatalf("NewGatewayServer failed: %v", err)
	}

	handler := server.securityHeadersMiddleware(server)

	// Test 1: root "/" returns index.html
	reqRoot := httptest.NewRequest(http.MethodGet, "/", nil)
	rrRoot := httptest.NewRecorder()
	handler.ServeHTTP(rrRoot, reqRoot)

	if rrRoot.Code != http.StatusOK {
		t.Errorf("Expected status 200 for root, got %d", rrRoot.Code)
	}
	if !strings.Contains(rrRoot.Body.String(), "Panama PortOps-AI Test Portal") {
		t.Errorf("Expected index.html content on root")
	}

	// Test 2: unknown frontend route falls back to SPA index.html
	reqSPA := httptest.NewRequest(http.MethodGet, "/dashboard/customs", nil)
	rrSPA := httptest.NewRecorder()
	handler.ServeHTTP(rrSPA, reqSPA)

	if rrSPA.Code != http.StatusOK {
		t.Errorf("Expected status 200 for SPA route, got %d", rrSPA.Code)
	}
	if !strings.Contains(rrSPA.Body.String(), "Panama PortOps-AI Test Portal") {
		t.Errorf("Expected index.html content on SPA fallback")
	}
}

func TestRateLimiter(t *testing.T) {
	rl := NewRateLimiter(2.0, 3.0) // 2 tokens/sec, burst 3
	ip := "192.168.1.100"

	// Initial burst of 3 should succeed
	if !rl.Allow(ip) {
		t.Errorf("Request 1 should be allowed")
	}
	if !rl.Allow(ip) {
		t.Errorf("Request 2 should be allowed")
	}
	if !rl.Allow(ip) {
		t.Errorf("Request 3 should be allowed")
	}

	// 4th immediate request should be rejected
	if rl.Allow(ip) {
		t.Errorf("Request 4 exceeded burst and should be rejected")
	}
}

func TestAppBrowserPolicyAndUntrustedCORS(t *testing.T) {
	staticDir, cleanup := setupTestEnvironment(t)
	defer cleanup()
	server, err := NewGatewayServer("8000", "http://127.0.0.1:8001", staticDir)
	if err != nil {
		t.Fatal(err)
	}
	handler := server.securityHeadersMiddleware(server)
	for _, origin := range []string{"https://example.com", "http://localhost:8000.evil.example", "null"} {
		rr := httptest.NewRecorder()
		req := httptest.NewRequest(http.MethodOptions, "http://127.0.0.1:8000/api/config", nil)
		req.Header.Set("Origin", origin)
		handler.ServeHTTP(rr, req)
		if rr.Code != http.StatusForbidden || rr.Header().Get("Access-Control-Allow-Origin") != "" {
			t.Fatalf("trusted origin %s: %d", origin, rr.Code)
		}
	}
	rr := httptest.NewRecorder()
	handler.ServeHTTP(rr, httptest.NewRequest(http.MethodGet, "/app", nil))
	if rr.Code != 200 {
		t.Fatal(rr.Code)
	}
	for name, value := range browserSecurityHeaders {
		if rr.Header().Get(name) != value {
			t.Fatalf("missing %s", name)
		}
	}
	request := httptest.NewRequest(http.MethodOptions, "http://127.0.0.1:8000/api/config", nil)
	request.Header.Set("Origin", "http://127.0.0.1:8000")
	rr = httptest.NewRecorder()
	handler.ServeHTTP(rr, request)
	if rr.Code != 204 || rr.Header().Get("Access-Control-Allow-Origin") != "http://127.0.0.1:8000" {
		t.Fatal("same origin rejected")
	}
}

func TestProxyCannotRestorePermissiveCORSOrDuplicatePolicy(t *testing.T) {
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-Forwarded-Host") != "127.0.0.1:8000" || r.Header.Get("X-Forwarded-Proto") != "http" {
			t.Error("incorrect forwarded origin")
		}
		w.Header().Set("Access-Control-Allow-Origin", "https://example.com")
		w.Header().Set("Access-Control-Allow-Credentials", "true")
		w.Header().Set("X-Frame-Options", "SAMEORIGIN")
		w.Header().Set("Content-Security-Policy", "default-src *")
		w.WriteHeader(200)
	}))
	defer upstream.Close()
	server, err := NewGatewayServer("8000", upstream.URL, t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	request := httptest.NewRequest(http.MethodGet, "http://127.0.0.1:8000/api/config", nil)
	request.Header.Set("Origin", "https://example.com")
	request.Header.Set("X-Forwarded-Host", "evil.example")
	rr := httptest.NewRecorder()
	server.securityHeadersMiddleware(server).ServeHTTP(rr, request)
	if rr.Header().Get("Access-Control-Allow-Origin") != "" {
		t.Fatal("upstream CORS leaked")
	}
	for name, value := range browserSecurityHeaders {
		if len(rr.Header().Values(name)) != 1 || rr.Header().Get(name) != value {
			t.Fatalf("policy duplicated or replaced: %s", name)
		}
	}
}

func TestWorkspaceDocumentsDoNotRedirectToOperationalPage(t *testing.T) {
	dir := t.TempDir()
	if err := os.MkdirAll(filepath.Join(dir, "workspace"), 0755); err != nil {
		t.Fatal(err)
	}
	os.WriteFile(filepath.Join(dir, "index.html"), []byte("operations"), 0644)
	os.WriteFile(filepath.Join(dir, "workspace", "index.html"), []byte("management"), 0644)
	server, err := NewGatewayServer("8000", "http://127.0.0.1:8001", dir)
	if err != nil {
		t.Fatal(err)
	}
	for _, url := range []string{"/static/workspace/", "/static/workspace/index.html"} {
		rr := httptest.NewRecorder()
		server.ServeHTTP(rr, httptest.NewRequest(http.MethodGet, url, nil))
		if rr.Code != 200 || rr.Body.String() != "management" || rr.Header().Get("Location") != "" {
			t.Fatalf("%s: %d %s", url, rr.Code, rr.Body.String())
		}
	}
}
