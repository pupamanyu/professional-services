output "druid_router" {
  description = "Outputs the private IP address of the node"
  value       = "${google_compute_instance.druid-router.*.network_interface.0.network_ip}"
}

output "instance_ip" {
  description = "Outputs the public IP address of the node"
  value       = "${google_compute_instance.druid-router.*.network_interface.0.access_config.0.nat_ip}"
}