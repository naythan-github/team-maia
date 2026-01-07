#Requires -Modules Az.Accounts, Az.Resources

<#
.SYNOPSIS
    Discover and document all accessible Azure environments.

.DESCRIPTION
    Queries all accessible Azure subscriptions, identifies environment types,
    and outputs markdown-formatted inventory for documentation updates.

.PARAMETER OutputPath
    Path where the markdown inventory will be saved.
    Default: ./azure_environment_inventory.md

.PARAMETER UpdateProtocol
    If specified, updates the Azure Environment Discovery Protocol file
    with the latest inventory data.

.EXAMPLE
    ./environment_discovery.ps1 -OutputPath "azure_environments.md"

.EXAMPLE
    ./environment_discovery.ps1 -UpdateProtocol

.NOTES
    Author: Azure Operations Engineer Agent / SRE Principal Engineer
    Last Updated: 2026-01-07
    Requires: Az.Accounts, Az.Resources PowerShell modules
#>

param(
    [string]$OutputPath = "./azure_environment_inventory.md",
    [switch]$UpdateProtocol
)

# Error handling
$ErrorActionPreference = "Stop"

Write-Host "🔍 Discovering Azure environments..." -ForegroundColor Cyan

try {
    # Get all enabled subscriptions
    Write-Host "📋 Querying subscriptions..." -ForegroundColor Gray
    $subscriptions = Get-AzSubscription | Where-Object {$_.State -eq 'Enabled'}

    if ($subscriptions.Count -eq 0) {
        Write-Warning "No enabled subscriptions found. Run 'az login' first."
        exit 1
    }

    Write-Host "   Found $($subscriptions.Count) subscription(s)" -ForegroundColor Gray

    # Classify environments (Sandbox vs Customer)
    $inventory = foreach ($sub in $subscriptions) {
        Write-Host "   Processing: $($sub.Name)..." -ForegroundColor Gray

        # Set context
        $context = Set-AzContext -Subscription $sub.Id -ErrorAction SilentlyContinue

        if (-not $context) {
            Write-Warning "Could not set context for subscription: $($sub.Name)"
            continue
        }

        # Get tenant info
        $tenant = Get-AzTenant -TenantId $sub.TenantId -ErrorAction SilentlyContinue

        # Get resource groups
        $resourceGroups = Get-AzResourceGroup -ErrorAction SilentlyContinue

        # Determine environment type
        $envType = if ($sub.Name -match 'Visual Studio|Dev|Test|Sandbox') {
            "Sandbox/Internal"
        } elseif ($tenant.DefaultDomain -eq 'Orrogroup.onmicrosoft.com') {
            "Internal"
        } else {
            "Customer"
        }

        # Build result object
        [PSCustomObject]@{
            EnvironmentType = $envType
            SubscriptionName = $sub.Name
            SubscriptionId = $sub.Id
            TenantName = if ($tenant) { $tenant.DisplayName } else { "Unknown" }
            TenantDomain = if ($tenant) { $tenant.DefaultDomain } else { "Unknown" }
            TenantId = $sub.TenantId
            ResourceGroupCount = if ($resourceGroups) { $resourceGroups.Count } else { 0 }
            ResourceGroups = if ($resourceGroups) { ($resourceGroups.ResourceGroupName -join ', ') } else { "None" }
        }
    }

    # Export markdown table
    Write-Host "📝 Generating markdown inventory..." -ForegroundColor Cyan

    $internalEnvs = $inventory | Where-Object {$_.EnvironmentType -ne 'Customer'}
    $customerEnvs = $inventory | Where-Object {$_.EnvironmentType -eq 'Customer'}

    $markdown = @"
# Azure Environment Inventory

**Generated**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
**Total Subscriptions**: $($inventory.Count)

## Internal/Sandbox Environments

| Subscription Name | Subscription ID | Tenant | Resource Groups |
|-------------------|-----------------|--------|-----------------|
$(if ($internalEnvs) {
    ($internalEnvs | ForEach-Object {
        "| $($_.SubscriptionName) | $($_.SubscriptionId) | $($_.TenantDomain) | $($_.ResourceGroups) |"
    }) -join "`n"
} else {
    "| None | - | - | - |"
})

## Customer Environments

| Subscription Name | Subscription ID | Tenant | Resource Groups |
|-------------------|-----------------|--------|-----------------|
$(if ($customerEnvs) {
    ($customerEnvs | ForEach-Object {
        "| $($_.SubscriptionName) | $($_.SubscriptionId) | $($_.TenantDomain) | $($_.ResourceGroups) |"
    }) -join "`n"
} else {
    "| None | - | - | - |"
})

---

**Discovery Script**: `claude/tools/azure_operations/environment_discovery.ps1`
**Protocol Documentation**: `claude/context/protocols/azure_environment_discovery.md`
"@

    # Save to file
    $markdown | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-Host "✅ Environment inventory saved to: $OutputPath" -ForegroundColor Green

    # Display summary
    Write-Host "`n📊 Summary:" -ForegroundColor Cyan
    Write-Host "   Internal/Sandbox: $($internalEnvs.Count)" -ForegroundColor Gray
    Write-Host "   Customer: $($customerEnvs.Count)" -ForegroundColor Gray
    Write-Host "   Total: $($inventory.Count)" -ForegroundColor Gray

    # Optional: Update protocol file
    if ($UpdateProtocol) {
        Write-Host "`n🔄 Updating protocol file..." -ForegroundColor Cyan
        $protocolPath = Join-Path $PSScriptRoot "../../context/protocols/azure_environment_discovery.md"

        if (Test-Path $protocolPath) {
            Write-Host "   Protocol file update not yet implemented" -ForegroundColor Yellow
            Write-Host "   Manually update: $protocolPath" -ForegroundColor Yellow
        } else {
            Write-Warning "Protocol file not found at: $protocolPath"
        }
    }

} catch {
    Write-Error "❌ Discovery failed: $_"
    Write-Error $_.ScriptStackTrace
    exit 1
}

Write-Host "`n✅ Discovery complete!" -ForegroundColor Green
