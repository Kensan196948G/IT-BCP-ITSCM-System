# IT-BCP-ITSCM-System Terraform Variables
# All configurable parameters for multi-region Azure deployment

variable "environment" {
  description = "Deployment environment (development, staging, production)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "resource_group_name" {
  description = "Name of the Azure Resource Group for all BCP-ITSCM resources"
  type        = string
  default     = "bcp-itscm-rg"
}

variable "resource_group_location" {
  description = "Primary Azure region for the resource group"
  type        = string
  default     = "japaneast"
}

variable "postgres_admin_password" {
  description = "Administrator password for PostgreSQL Flexible Server"
  type        = string
  sensitive   = true
  default     = ""
}

variable "postgres_admin_username" {
  description = "Administrator username for PostgreSQL Flexible Server"
  type        = string
  default     = "bcpadmin"
}

variable "primary_region" {
  description = "Primary Azure region for active deployment"
  type        = string
  default     = "japaneast"
}

variable "dr_region" {
  description = "Disaster recovery Azure region for standby deployment"
  type        = string
  default     = "japanwest"
}

variable "primary_container_replicas" {
  description = "Number of container app replicas in the primary region"
  type        = number
  default     = 3
}

variable "dr_container_replicas" {
  description = "Number of container app replicas in the DR region"
  type        = number
  default     = 2
}

variable "primary_postgres_sku" {
  description = "PostgreSQL SKU for the primary region"
  type        = string
  default     = "GP_Standard_D4s_v3"
}

variable "dr_postgres_sku" {
  description = "PostgreSQL SKU for the DR region"
  type        = string
  default     = "GP_Standard_D2s_v3"
}

variable "primary_redis_sku" {
  description = "Redis cache SKU for the primary region"
  type        = string
  default     = "Premium"
}

variable "dr_redis_sku" {
  description = "Redis cache SKU for the DR region"
  type        = string
  default     = "Standard"
}

variable "redis_capacity" {
  description = "Redis cache capacity (family size)"
  type        = number
  default     = 1
}

variable "frontdoor_sku" {
  description = "Azure Front Door SKU name"
  type        = string
  default     = "Premium_AzureFrontDoor"
}

variable "app_version" {
  description = "Application version tag for deployment tracking"
  type        = string
  default     = "0.1.0"
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default = {
    Project   = "IT-BCP-ITSCM-System"
    ManagedBy = "Terraform"
  }
}

variable "log_analytics_retention_days" {
  description = "Log Analytics workspace retention period in days"
  type        = number
  default     = 90
}

variable "backup_retention_days" {
  description = "Database backup retention period in days"
  type        = number
  default     = 35
}

variable "ssl_enforcement_enabled" {
  description = "Whether SSL enforcement is enabled on PostgreSQL"
  type        = bool
  default     = true
}

variable "auto_failover_enabled" {
  description = "Whether automatic failover is enabled for DR"
  type        = bool
  default     = true
}
