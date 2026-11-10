$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = [Microsoft.Office.Interop.Word.WdAlertLevel]::wdAlertsNone

try {
    $doc = $word.Documents.Open("c:\Users\ЕвполовВ\Desktop\titulni_list\Титульный_лист_ИТОГ.docx")
    $pdfPath = "c:\Users\ЕвполовВ\Desktop\titulni_list\Титульный_лист_ИТОГ.pdf"
    $doc.SaveAs([ref]$pdfPath, [ref]17)
    Write-Host "Exported Титульный_лист_ИТОГ.pdf successfully."
    $doc.Close([ref]0)
} catch {
    Write-Error $_
} finally {
    $word.Quit()
}
