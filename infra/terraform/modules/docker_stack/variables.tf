variable "project_prefix" {
  type        = string
  default     = "portops"
  description = "Prefix for container and resource names"
}

variable "network_name" {
  type        = string
  default     = "portops-mlops-network"
  description = "Docker network name"
}

variable "redis_port" {
  type        = number
  default     = 6379
  description = "Host port for Redis"
}

variable "db_port" {
  type        = number
  default     = 5432
  description = "Host port for TimescaleDB"
}

variable "db_user" {
  type        = string
  default     = "postgres"
  description = "TimescaleDB user"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "TimescaleDB password"
}

variable "db_name" {
  type        = string
  default     = "amp_portops"
  description = "TimescaleDB database name"
}
