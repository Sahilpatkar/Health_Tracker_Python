output "public_ip" {
  value = aws_eip.static_ip.public_ip
}