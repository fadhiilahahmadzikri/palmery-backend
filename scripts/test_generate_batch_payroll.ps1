$ErrorActionPreference = "Stop"
$BaseUrl = "http://localhost:8000/api/v1"

Write-Host "========================================="
Write-Host " REAL-WORLD API TEST: BATCH PAYROLL      "
Write-Host "========================================="

# Skip server check as user is running it independently

# 2. Get the July Period
Write-Host "`n[2] Fetching periods..." -ForegroundColor Cyan
$periods = Invoke-RestMethod -Uri "$BaseUrl/payroll/periods/open" -Method Post -Body '{"year": 2026, "month": 7}' -ContentType "application/json"
$july_period_id = $periods.id
Write-Host "    Found July 2026 Period ID: $july_period_id" -ForegroundColor Green

# 3. Generate Bulk Payroll Batch for July
Write-Host "`n[3] Generating Bulk Payroll Batch for July 2026..." -ForegroundColor Cyan
try {
    $batch = Invoke-RestMethod -Uri "$BaseUrl/payroll/periods/$july_period_id/batches/generate" -Method Post
    Write-Host "    Batch ID: $($batch.id)" -ForegroundColor Green
    Write-Host "    Status: $($batch.status)" -ForegroundColor Green
    Write-Host "    Generated At: $($batch.generated_at)" -ForegroundColor Green
    
    Write-Host "    -- History Log --" -ForegroundColor Yellow
    foreach ($h in $batch.status_history) {
        Write-Host "       $($h.changed_at) | $($h.from_status) -> $($h.to_status) (By: $($h.changed_by))"
    }
} catch {
    Write-Host "    Failed to generate batch. Exception: $_" -ForegroundColor Red
    exit 1
}

# 4. Fetch the Summaries in the Batch
Write-Host "`n[4] Fetching all summaries generated in the Batch..." -ForegroundColor Cyan
try {
    $summaries = Invoke-RestMethod -Uri "$BaseUrl/payroll/batches/$($batch.id)/summaries" -Method Get
    Write-Host "    Successfully fetched $($summaries.Count) payroll summaries from the database." -ForegroundColor Green
    
    if ($summaries.Count -gt 0) {
        $first = $summaries[0]
        Write-Host "    Sample Summary (First Harvester):" -ForegroundColor Yellow
        Write-Host "      Harvester ID: $($first.harvester_id)"
        Write-Host "      Total Valid Bunches: $($first.total_valid_bunch_count)"
        Write-Host "      Total Net Tonnage: $($first.total_net_tonnage_kg) KG"
        Write-Host "      Total Net Pay: Rp $($first.total_net_pay_rupiah)"
        Write-Host "      Tiers attached: $($first.tier_details.Count)"
        Write-Host "      Daily records attached: $($first.daily_records.Count)"
    }
} catch {
    Write-Host "    Failed to fetch summaries. Exception: $_" -ForegroundColor Red
    exit 1
}

# 5. Approve the Batch
Write-Host "`n[5] Transitioning Batch Status to 'Approved'..." -ForegroundColor Cyan
try {
    $approved_batch = Invoke-RestMethod -Uri "$BaseUrl/payroll/batches/$($batch.id)/status?status=approved&changed_by=HR_Manager&notes=Looks_Good" -Method Post
    Write-Host "    Status updated to: $($approved_batch.status)" -ForegroundColor Green
} catch {
    Write-Host "    Failed to update status. Exception: $_" -ForegroundColor Red
    exit 1
}

# 6. Test Export Bulk Endpoint
Write-Host "`n[6] Testing Export Batch (ZIP with PDFs)..." -ForegroundColor Cyan
try {
    $exportFile = "test_export_batch.zip"
    Invoke-RestMethod -Uri "$BaseUrl/payroll/batches/$($batch.id)/export?format=pdf" -Method Get -OutFile $exportFile
    
    $fileInfo = Get-Item $exportFile
    Write-Host "    Successfully downloaded bulk export ZIP!" -ForegroundColor Green
    Write-Host "    File Size: $($fileInfo.Length) bytes" -ForegroundColor Yellow
    
    # Cleanup
    Remove-Item $exportFile
} catch {
    Write-Host "    Failed to export batch. Exception: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================="
Write-Host " BATCH PAYROLL API E2E TEST PASSED!      " -ForegroundColor Green
Write-Host "========================================="
