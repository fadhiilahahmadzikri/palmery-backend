$periodId = "e3cdaa29-ff33-4712-bc9b-44770d8fd337"
$harvesterId = "68017715-be46-4b66-94c4-945538494ce8"
$url = "http://127.0.0.1:8000/api/v1/payroll/periods/$periodId/generate/$harvesterId"

Write-Host "Testing POST endpoint: $url"
try {
    $response = Invoke-RestMethod -Uri $url -Method Post -ContentType "application/json"
    Write-Host "SUCCESS: Endpoint returned status 200 OK!" -ForegroundColor Green
    
    # Test checking if daily_records are present
    $recordCount = $response.daily_records.Count
    if ($null -ne $recordCount) {
        Write-Host "VALIDATION PASSED: Found $recordCount daily_records in response." -ForegroundColor Green
    } else {
        Write-Host "WARNING: daily_records property is missing or empty." -ForegroundColor Yellow
    }

    # Print summary
    Write-Host "--------------------------------------------------"
    Write-Host "Summary ID           : $($response.id)"
    Write-Host "Total Janjang Valid  : $($response.total_valid_bunch_count)"
    Write-Host "Net Tonnage (kg)     : $($response.total_net_tonnage_kg)"
    Write-Host "Total Net Pay        : Rp $($response.total_net_pay_rupiah)"
    Write-Host "--------------------------------------------------"

} catch {
    Write-Host "ERROR: Failed to call endpoint" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails -ne $null) {
        Write-Host $_.ErrorDetails.Message -ForegroundColor Red
    }
    exit 1
}
