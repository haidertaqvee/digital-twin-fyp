$ErrorActionPreference = 'SilentlyContinue'

Write-Output "=== whoami ==="
whoami

Write-Output ""
Write-Output "=== ArcGIS targets ==="
$targets = @(
  'C:\Users\Admin\Documents\ArcGIS Pro 2.8',
  'C:\Users\Admin\AppData\Local\Temp\Rar$EXa7496.26594'
)
foreach ($t in $targets) {
  if (Test-Path -LiteralPath $t) {
    $s = (Get-ChildItem -LiteralPath $t -Recurse -File -Force | Measure-Object Length -Sum).Sum
    Write-Output ("{0,8:N2} GB  {1}" -f ($s/1GB), $t)
  } else {
    Write-Output ("MISSING  " + $t)
  }
}

Write-Output ""
Write-Output "=== writability test on C:\Users\Admin ==="
$probe = 'C:\Users\Admin\.__wtest_probe'
try {
  New-Item -Path $probe -ItemType File -Force -ErrorAction Stop | Out-Null
  Remove-Item -LiteralPath $probe -Force
  Write-Output "WRITABLE"
} catch {
  Write-Output ("NOT WRITABLE: " + $_.Exception.Message)
}

Write-Output ""
Write-Output "=== C: free space now ==="
$d = Get-PSDrive C
Write-Output ("Used {0:N2} GB | Free {1:N2} GB" -f ($d.Used/1GB), ($d.Free/1GB))
