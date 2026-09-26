variable "db_password" {
  type        = string
  sensitive   = true
  description = "Production TimescaleDB password"
}

variable "grafana_admin_password" {
  type        = string
  sensitive   = true
  description = "Production Grafana admin password"
}
