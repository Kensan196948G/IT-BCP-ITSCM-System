# IT-BCP-ITSCM-System Infrastructure
# Azure Multi-Region Deployment (East Japan + West Japan)

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }

  backend "azurerm" {
    resource_group_name  = "bcp-terraform-state"
    storage_account_name = "bcpterraformstate"
    container_name       = "tfstate"
    key                  = "bcp-itscm.tfstate"
  }
}

provider "azurerm" {
  features {}
}

# Variables
variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
  default     = "bcp-itscm-rg"
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = "japaneast"

  tags = {
    Project     = "IT-BCP-ITSCM-System"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# East Japan (Primary)
module "east_japan" {
  source = "./modules/region"

  location        = "japaneast"
  resource_prefix = "bcp-east"
  resource_group  = azurerm_resource_group.main.name
  is_primary      = true

  container_apps_replicas = 3
  postgres_sku            = "GP_Standard_D4s_v3"
  redis_sku               = "Premium"
  redis_capacity          = 1

  tags = {
    Region = "East Japan"
    Role   = "Primary"
  }
}

# West Japan (Standby / DR)
module "west_japan" {
  source = "./modules/region"

  location        = "japanwest"
  resource_prefix = "bcp-west"
  resource_group  = azurerm_resource_group.main.name
  is_primary      = false

  container_apps_replicas = 2
  postgres_sku            = "GP_Standard_D2s_v3"
  redis_sku               = "Standard"
  redis_capacity          = 1

  tags = {
    Region = "West Japan"
    Role   = "Standby"
  }
}

# Azure Front Door (Global Load Balancer + WAF)
resource "azurerm_cdn_frontdoor_profile" "main" {
  name                = "bcp-frontdoor"
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = "Premium_AzureFrontDoor"

  tags = {
    Project = "IT-BCP-ITSCM-System"
  }
}

resource "azurerm_cdn_frontdoor_endpoint" "main" {
  name                     = "bcp-itscm"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.main.id
}

# Outputs
output "frontdoor_endpoint" {
  value = azurerm_cdn_frontdoor_endpoint.main.host_name
}

output "east_japan_app_url" {
  value = module.east_japan.app_url
}

output "west_japan_app_url" {
  value = module.west_japan.app_url
}
