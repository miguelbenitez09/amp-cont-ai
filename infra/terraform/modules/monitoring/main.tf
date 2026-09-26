# Module: monitoring (Prometheus + Grafana)
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

resource "docker_volume" "prometheus_data" {
  name = "${var.project_prefix}-prometheus-data"
}

resource "docker_volume" "grafana_data" {
  name = "${var.project_prefix}-grafana-data"
}

resource "docker_image" "prometheus" {
  name         = "prom/prometheus:v2.54.1"
  keep_locally = true
}

resource "docker_container" "prometheus" {
  name    = "${var.project_prefix}-prometheus"
  image   = docker_image.prometheus.image_id
  restart = "unless-stopped"
  ports {
    internal = 9090
    external = var.prometheus_port
  }
  volumes {
    volume_name    = docker_volume.prometheus_data.name
    container_path = "/prometheus"
  }
}

resource "docker_image" "grafana" {
  name         = "grafana/grafana:11.2.0"
  keep_locally = true
}

resource "docker_container" "grafana" {
  name    = "${var.project_prefix}-grafana"
  image   = docker_image.grafana.image_id
  restart = "unless-stopped"
  ports {
    internal = 3000
    external = var.grafana_port
  }
  env = [
    "GF_SECURITY_ADMIN_USER=${var.grafana_admin_user}",
    "GF_SECURITY_ADMIN_PASSWORD=${var.grafana_admin_password}"
  ]
  volumes {
    volume_name    = docker_volume.grafana_data.name
    container_path = "/var/lib/grafana"
  }
}
