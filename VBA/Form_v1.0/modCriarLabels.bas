Attribute VB_Name = "modCriarLabels"
Option Explicit

' Copie esta Sub e cole DENTRO do frmPrincipal no VBA.
' Depois remova este modulo (modCriarLabels).
'
' Private Sub CriarLabelsHdr()
'     Dim names, caps, pos, i As Long, lbl As Object
'     names = Array("lblHdrCompetencia", "lblHdrRegional", "lblHdrUnidade", "lblHdrHospital", _
'                   "lblHdrTitulo", "lblHdrNFe", "lblHdrStatusNFe", "lblHdrDataEnvio", _
'                   "lblHdrMotivoGlosa", "lblHdrFaturamento", "lblHdrGlosa", "lblHdrPerda", "lblHdrObservacao")
'     caps = Array("Competencia", "Regional", "Unidade", "Hospital", _
'                  "Titulo", "NFe", "Status NFe", "Dt Envio", _
'                  "Motivo Glosa", "Faturamento", "Glosa", "Perda", "Observacao")
'     pos = Array(20, 1320, 3320, 5320, 11320, 13320, 14920, 17320, 18920, 21320, 22920, 24520, 26120)
'     On Error Resume Next
'     For i = 0 To 12
'         Set lbl = Me.Controls(names(i))
'         If lbl Is Nothing Then
'             Set lbl = Me.Controls.Add("Forms.Label.1", names(i))
'             With lbl
'                 .Caption = caps(i)
'                 .Top = lstDados.Top - 200
'                 .Left = pos(i)
'                 .Width = 120
'                 .Height = 180
'                 .Font.Size = 8
'                 .Font.Bold = True
'                 .ForeColor = RGB(0, 118, 182)
'                 .TextAlign = fmTextAlignCenter
'                 .Visible = True
'             End With
'         End If
'     Next i
'     On Error GoTo 0
' End Sub
'
' Depois chame no inicio do UserForm_Initialize:
'     CriarLabelsHdr
'     ' Depois seus Me.lblHdr...Left = ...
