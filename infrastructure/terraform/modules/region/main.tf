# Regional Module - Azure Container Apps + PostgreSQL + Redis

variable "location" { type = string }
variable "resource_prefix" { type = string }
variable "resource_group" { type = string }
variable "is_primary" { type = bool }
variable "container_apps_replicas" { type = number }
variable "postgres_sku" { type = string }
variable "redis_sku" { type = string }
variable "redis_capacity" { type = number }
variable "tags" { type = map(string) }

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.resource_prefix}-logs"
  location            = var.location
  resource_group_name = var.resource_group
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

# Container Apps Environment
resource "azurerm_container_app_environment" "main" {
  name                       = "${var.resource_prefix}-env"
  location                   = var.location
  resource_group_name        = var.resource_group
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = var.tags
}

# Backend Container App
resource "azurerm_container_app" "backend" {
  name                         = "${var.resource_prefix}-backend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group
  revision_mode                = "Single"

  template {
    min_replicas = var.is_primary ? 2 : 1
    max_replicas = var.container_apps_replicas

    container {
      name   = "backend"
      image  = "ghcr.io/kensan196948g/bcp-itscm-backend:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "ENVIRONMENT"
        value = var.is_primary ? "production" : "standby"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = var.tags
}

# Frontend Container App
resource "azurerm_container_app" "frontend" {
  name                         = "${var.resource_prefix}-frontend"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.resource_group
  revision_mode                = "Single"

  template {
    min_replicas = var.is_primary ? 2 : 1
    max_replicas = var.container_apps_replicas

    container {
      name   = "frontend"
      image  = "ghcr.io/kensan196948g/bcp-itscm-frontend:latest"
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }

  ingress {
    external_enabled = true
    target_port      = 3000
    transport        = "http"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  tags = var.tags
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${var.resource_prefix}-pg"
  resource_group_name    = var.resource_group
  location               = var.location
  version                = "16"
  administrator_login    = "bcp_admin"
  administrator_password = var.is_primary ? "CHANGE_ME_IN_KEYVAULT" : null
  sku_name               = var.postgres_sku
  storage_mb             = 32768
  zone                   = "1"

  high_availability {
    mode = var.is_primary ? "ZoneRedundant" : "Disabled"
  }

  tags = var.tags
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = "bcp_itscm"
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "ja_JP.utf8"
}

# Redis Cache
resource "azurerm_redis_cache" "main" {
  name                = "${var.resource_prefix}-redis"
  location            = var.location
  resource_group_name = var.resource_group
  capacity            = var.redis_capacity
  family              = var.redis_sku == "Premium" ? "P" : "C"
  sku_name            = var.redis_sku
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
  tags                = var.tags
}

# Outputs
output "app_url" {
  value = azurerm_container_app.backend.ingress[0].fqdn
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "redis_hostname" {
  value = azurerm_redis_cache.main.hostname
}
