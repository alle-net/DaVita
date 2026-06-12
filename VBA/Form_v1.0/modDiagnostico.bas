Attribute VB_Name = "modDiagnostico"
Option Explicit

' Executar APOS abrir o frmPrincipal (com dados carregados)
Sub MostrarPosicoesCabecalhos()
    Dim cw, hd, i As Long, x As Double
    Dim raw As String
    
    On Error Resume Next
    raw = frmPrincipal.lstDados.ColumnWidths
    If Err.Number <> 0 Then
        MsgBox "Abra o frmPrincipal primeiro (faca login)", vbExclamation
        Exit Sub
    End If
    On Error GoTo 0
    
    cw = Split(raw, ";")
    If UBound(cw) <> 12 Then
        MsgBox "lstDados sem dados ou ColumnWidths invalido", vbExclamation
        Exit Sub
    End If
    
    hd = Array("Competencia", "Regional", "Unidade", "Hospital", _
               "Titulo", "NFe", "Status NFe", "Dt Envio", _
               "Motivo Glosa", "Faturamento", "Glosa", "Perda", "Observacao")
    
    Debug.Print "=== lstDados (do controle em runtime) ==="
    Debug.Print "Left=" & frmPrincipal.lstDados.Left & " Top=" & frmPrincipal.lstDados.Top
    Debug.Print "Width=" & frmPrincipal.lstDados.Width & " Height=" & frmPrincipal.lstDados.Height
    Debug.Print "ColumnWidths=" & raw
    
    x = frmPrincipal.lstDados.Left
    Debug.Print ""
    Debug.Print "Left | Top | Width | Caption"
    Debug.Print "----------------------------------------"
    
    For i = 0 To 12
        Debug.Print x & " | " & (frmPrincipal.lstDados.Top - 200) & _
                    " | " & (CDbl(cw(i)) * 20) & " | 180 | " & hd(i)
        x = x + CDbl(cw(i)) * 20
    Next i
    
    MsgBox "Posicoes no Immediate Window (Ctrl+G)", vbInformation, "OK"
End Sub
