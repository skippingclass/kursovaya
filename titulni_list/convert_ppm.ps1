Add-Type -AssemblyName System.Drawing

function Convert-PpmToPng([string]$ppmPath, [string]$pngPath) {
    $bytes = [System.IO.File]::ReadAllBytes($ppmPath)
    $i = 0
    # skip P6
    while ($bytes[$i] -ne 10 -and $bytes[$i] -ne 13) { $i++ }
    while ($bytes[$i] -eq 10 -or $bytes[$i] -eq 13 -or $bytes[$i] -eq 32) { $i++ }
    # read width
    $wStr = ""
    while ($bytes[$i] -ge 48 -and $bytes[$i] -le 57) { $wStr += [char]$bytes[$i]; $i++ }
    while ($bytes[$i] -eq 10 -or $bytes[$i] -eq 13 -or $bytes[$i] -eq 32) { $i++ }
    # read height
    $hStr = ""
    while ($bytes[$i] -ge 48 -and $bytes[$i] -le 57) { $hStr += [char]$bytes[$i]; $i++ }
    while ($bytes[$i] -eq 10 -or $bytes[$i] -eq 13 -or $bytes[$i] -eq 32) { $i++ }
    # read maxval
    while ($bytes[$i] -ge 48 -and $bytes[$i] -le 57) { $i++ }
    while ($bytes[$i] -eq 10 -or $bytes[$i] -eq 13) { $i++ }
    
    $w = [int]$wStr
    $h = [int]$hStr
    $bmp = New-Object System.Drawing.Bitmap($w, $h, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    $rect = New-Object System.Drawing.Rectangle(0, 0, $w, $h)
    $bmpData = $bmp.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::WriteOnly, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    
    $stride = $bmpData.Stride
    $ptr = $bmpData.Scan0
    $totalBytes = $stride * $h
    $rgbValues = New-Object byte[] $totalBytes
    
    $srcIdx = $i
    for ($y = 0; $y -lt $h; $y++) {
        $rowOffset = $y * $stride
        for ($x = 0; $x -lt $w; $x++) {
            $r = $bytes[$srcIdx]
            $g = $bytes[$srcIdx + 1]
            $b = $bytes[$srcIdx + 2]
            $srcIdx += 3
            $pixOffset = $rowOffset + $x * 3
            $rgbValues[$pixOffset] = $b
            $rgbValues[$pixOffset + 1] = $g
            $rgbValues[$pixOffset + 2] = $r
        }
    }
    [System.Runtime.InteropServices.Marshal]::Copy($rgbValues, 0, $ptr, $totalBytes)
    $bmp.UnlockBits($bmpData)
    $bmp.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Write-Output "Converted $ppmPath to $pngPath"
}

Convert-PpmToPng "$PSScriptRoot\img_20.ppm" "$PSScriptRoot\img_20.png"
Convert-PpmToPng "$PSScriptRoot\img_30.ppm" "$PSScriptRoot\img_30.png"
Convert-PpmToPng "$PSScriptRoot\img_37.ppm" "$PSScriptRoot\img_37.png"
Convert-PpmToPng "$PSScriptRoot\img_43.ppm" "$PSScriptRoot\img_43.png"
