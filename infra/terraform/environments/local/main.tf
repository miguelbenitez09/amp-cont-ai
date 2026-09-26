# Environment: Local Development
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

provider "docker" {}

module "docker_stack" {
  source         = "../../modules/docker_stack"
  project_prefix = "portops-dev"
  network_name   = "portops-dev-network"
  db_password    = "panama_portops_pass_dev"
  db_port        = 5432
  redis_port     = 6379
}

module "monitoring" {
  source          = "../../modules/monitoring"
  project_prefix  = "portops-dev"
  prometheus_port = 9090
  grafana_port    = 3000
}
