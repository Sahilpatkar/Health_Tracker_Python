variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile name (use for SSO / named credentials). Null uses the default credential chain."
  type        = string
  default     = null
  nullable    = true
}

variable "instance_type" {
  description = "EC2 instance type – t3.small is the minimum for Kafka + MySQL + API + Frontend"
  type        = string
  default     = "t3.small"
}

variable "ebs_size_gb" {
  description = "Size of the persistent EBS data volume in GB"
  type        = number
  default     = 20
}

variable "key_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to SSH into the instance (restrict to your IP)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "app_name" {
  description = "Name tag prefix for all resources"
  type        = string
  default     = "health-tracker"
}

# --- Application secrets (passed into the instance via .env) ---

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "groq_api_key" {
  description = "Groq API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "jwt_secret" {
  description = "JWT signing secret for FastAPI auth"
  type        = string
  sensitive   = true
  default     = "change-me-to-a-random-string"
}

variable "db_password" {
  description = "MySQL root & user password"
  type        = string
  sensitive   = true
  default     = "123456"
}
