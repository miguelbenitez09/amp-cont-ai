# Module: docker_stack
# Author: Desarrollado v1.0 Miguel Benítez
# License: GNU GPL-3.0 with Section 7 Mandatory Attribution

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.2"
    }
  }
}

resource "docker_network" "portops_network" {
  name = var.network_name
}

resource "docker_volume" "timescale_data" {
  name = "${var.project_prefix}-timescale-data"
}

resource "docker_volume" "redis_data" {
  name = "${var.project_prefix}-redis-data"
}

resource "docker_image" "redis" {
  name         = "redis:7.2.5-alpine"
  keep_locally = true
}

resource "docker_container" "redis" {
  name  = "${var.project_prefix}-redis"
  image = docker_image.redis.image_id
  restart = "unless-stopped"
  networks_advanced {
    name = docker_network.portops_network.name
  }
  ports {
    internal = 6379
    external = var.redis_port
  }
}

resource "docker_image" "timescaledb" {
  name         = "timescale/timescaledb:latest-pg16"
  keep_locally = true
}

resource "docker_container" "timescaledb" {
  name  = "${var.project_prefix}-timescaledb"
  image = docker_image.timescaledb.image_id
  restart = "unless-stopped"
  networks_advanced {
    name = docker_network.portops_network.name
  }
  env = [
    "POSTGRES_USER=${var.db_user}",
    "POSTGRES_PASSWORD=${var.db_password}",
    "POSTGRES_DB=${var.db_name}"
  ]
  ports {
    internal = 5432
    external = var.db_port
  }
  volumes {
    volume_name    = docker_volume.timescale_data.name
    container_path = "/var/lib/postgresql/data"
  }
}
