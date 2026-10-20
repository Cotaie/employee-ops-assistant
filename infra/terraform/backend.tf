terraform {
  backend "s3" {
    bucket       = "employee-assitant-ops-terraform-state-euc1"
    key          = "terraform.tfstate"
    region       = "eu-central-1"
    use_lockfile = true
  }
}
