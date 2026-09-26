variable "project_prefix" {
  type        = string
  default     = "portops"
  description = "Prefix for container names"
}

variable "prometheus_port" {
  type        = number
  default     = 9090
  description = "Host port for Prometheus"
}

variable "grafana_port" {
  type        = number
  default     = 3000
  description = "Host port for Grafana"
}

variable "grafana_admin_user" {
  type        = string
  default     = "admin"
  description = "Admin username for Grafana"
}

variable "grafana_admin_password" {
  type        = string
  sensitive   = true
  default     = "portops_grafana_pass"
  description = "Admin password for Grafana"
}
