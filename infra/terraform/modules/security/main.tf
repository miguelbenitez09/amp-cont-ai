# Module: security (Wazuh Zero-Trust SIEM)
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

resource "docker_volume" "wazuh_manager_data" {
  name = "${var.project_prefix}-wazuh-manager-data"
}

resource "docker_volume" "wazuh_indexer_data" {
  name = "${var.project_prefix}-wazuh-indexer-data"
}

resource "docker_image" "wazuh_manager" {
  name         = "wazuh/wazuh-manager:4.9.0"
  keep_locally = true
}

resource "docker_container" "wazuh_manager" {
  name    = "${var.project_prefix}-wazuh-manager"
  image   = docker_image.wazuh_manager.image_id
  restart = "unless-stopped"
  ports {
    internal = 1514
    external = 1514
  }
  ports {
    internal = 55000
    external = 55000
  }
  volumes {
    volume_name    = docker_volume.wazuh_manager_data.name
    container_path = "/var/ossec/data"
  }
}

resource "docker_image" "wazuh_indexer" {
  name         = "wazuh/wazuh-indexer:4.9.0"
  keep_locally = true
}

resource "docker_container" "wazuh_indexer" {
  name    = "${var.project_prefix}-wazuh-indexer"
  image   = docker_image.wazuh_indexer.image_id
  restart = "unless-stopped"
  ports {
    internal = 9200
    external = 9200
  }
  env = [
    "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"
  ]
  volumes {
    volume_name    = docker_volume.wazuh_indexer_data.name
    container_path = "/var/lib/wazuh-indexer"
  }
}
