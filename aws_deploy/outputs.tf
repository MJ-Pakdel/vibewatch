output "public_ip" {
  description = "Public IP of the vibewatch server"
  value       = aws_instance.vibewatch.public_ip
} 