output "public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_eip.app.public_ip
}

output "frontend_url" {
  description = "React frontend URL"
  value       = "http://${aws_eip.app.public_ip}:3000"
}

output "api_url" {
  description = "FastAPI backend URL"
  value       = "http://${aws_eip.app.public_ip}:8000"
}

output "api_docs_url" {
  description = "FastAPI Swagger docs"
  value       = "http://${aws_eip.app.public_ip}:8000/docs"
}

output "kafka_ui_url" {
  description = "Kafka UI URL"
  value       = "http://${aws_eip.app.public_ip}:8080"
}

output "ssh_command" {
  description = "SSH into the instance"
  value       = "ssh -i ~/.ssh/${var.key_name}.pem ec2-user@${aws_eip.app.public_ip}"
}
