Add-Type -AssemblyName System.Drawing

$imgNames = @("img_20.png", "img_30.png", "img_37.png", "img_43.png")

foreach ($name in $imgNames) {
    $bmp = [System.Drawing.Bitmap]::FromFile("c:\Users\ЕвполовВ\Desktop\titulni_list\$name")
    Write-Host "=== $name $($bmp.Width)x$($bmp.Height) ==="
    $bmp.Dispose()
}
