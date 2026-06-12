Attribute VB_Name = "AjustarHeaders"
Option Explicit

' Execute no Immediate Window APOS fazer login:
'   Call AjustarHeaders
'
' Se ficar desalinhado, mude o FACTOR (teste: 1, 5, 10, 15, 20)

Sub AjustarHeaders()
    Const FACTOR = 20
    Const TOP_OFFSET = 200
    
    Dim cw, hd, i As Long, x As Double, lbl As Object
    Dim frm As Object, lb As Object
    
    On Error Resume Next
    Set frm = frmPrincipal
    If frm Is Nothing Then
        MsgBox "Abra o frmPrincipal primeiro (faca login)"
        Exit Sub
    End If
    Set lb = frm.lstDados
    If lb Is Nothing Then Exit Sub
    
    cw = Split(lb.ColumnWidths, ";")
    hd = Array("Competencia", "Regional", "Unidade", "Hospital", _
               "Titulo", "NFe", "Status NFe", "Dt Envio", _
               "Motivo Glosa", "Faturamento", "Glosa", "Perda", "Observacao")
    
    ' Mostra no Immediate Window as posicoes
    Debug.Print "--- Posicoes (FACTOR=" & FACTOR & ") ---"
    Debug.Print "Label | Left | Width"
    
    x = lb.Left
    For i = 0 To 12
        Set lbl = Nothing
        Set lbl = frm.Controls("lblHdr" & i)
        If lbl Is Nothing Then
            Set lbl = frm.Controls.Add("Forms.Label.1", "lblHdr" & i)
        End If
        If Not lbl Is Nothing Then
            Dim w As Double
            w = CDbl(cw(i)) * FACTOR
            With lbl
                .Caption = hd(i)
                .Left = x
                .Top = lb.Top - TOP_OFFSET
                .Width = w
                .Height = 180
                .Font.Size = 8
                .Font.Bold = True
                .ForeColor = RGB(0, 118, 182)
                .TextAlign = fmTextAlignCenter
                .Visible = True
                .ZOrder (0)
            End With
            Debug.Print hd(i) & " | " & x & " | " & w
        End If
        x = x + CDbl(cw(i)) * FACTOR
    Next i
    On Error GoTo 0
    MsgBox "Headers criados (FACTOR=" & FACTOR & ")"
End Sub
