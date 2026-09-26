output "network_id" {
  value       = docker_network.portops_network.id
  description = "Docker network ID"
}

output "redis_container_id" {
  value       = docker_container.redis.id
  description = "Redis container ID"
}

output "timescale_container_id" {
  value       = docker_container.timescaledb.id
  description = "TimescaleDB container ID"
}
