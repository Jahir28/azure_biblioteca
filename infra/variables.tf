variable "location" {
  description = "Azure region for all resources."
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Resource group name."
  type        = string
  default     = "rg-azure-biblioteca-dev"
}

variable "acr_name" {
  description = "Azure Container Registry name."
  type        = string
  default     = "acrazurebibliotecadev"
}

variable "container_group_name" {
  description = "Azure Container Instance group name."
  type        = string
  default     = "aci-azure-biblioteca-dev"
}

variable "storage_account_name" {
  description = "Storage account name for the SQLite Azure File share."
  type        = string
  default     = "stazurebibliotecadev"
}

variable "backend_image" {
  description = "Backend image repository name."
  type        = string
  default     = "azure-biblioteca-backend"
}

variable "frontend_image" {
  description = "Frontend image repository name."
  type        = string
  default     = "azure-biblioteca-frontend"
}

variable "image_tag" {
  description = "Image tag to deploy."
  type        = string
  default     = "latest"
}
