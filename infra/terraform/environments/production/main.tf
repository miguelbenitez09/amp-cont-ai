# Environment: Production
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
  project_prefix = "portops-prod"
  network_name   = "portops-prod-network"
  db_password    = var.db_password
  db_port        = 5432
  redis_port     = 6379
}

module "monitoring" {
  source                 = "../../modules/monitoring"
  project_prefix         = "portops-prod"
  prometheus_port        = 9090
  grafana_port           = 3000
  grafana_admin_password = var.grafana_admin_password
}

module "security" {
  source         = "../../modules/security"
  project_prefix = "portops-prod"
}
