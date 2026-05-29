Attribute VB_Name = "modAutenticacao"
Option Explicit

Public UsuarioAtual As Long
Public EmailAtual As String

Public Function VerificarCredenciais(pEmail As String, pSenha As String) As Boolean
    VerificarCredenciais = (pSenha = "102030")
End Function

Public Function ObterIdUsuario(pEmail As String) As Long
    Dim ws As Worksheet, tb As ListObject, dr As Range
    Dim i As Long
    On Error GoTo ErrHandler
    Set ws = ThisWorkbook.Worksheets("dUsuarios")
    Set tb = ws.ListObjects("dUsuario")
    If tb.DataBodyRange Is Nothing Then ObterIdUsuario = 0: Exit Function
    Set dr = tb.DataBodyRange
    For i = 1 To dr.Rows.Count
        If LCase(Trim(dr.Cells(i, 2).Value)) = LCase(Trim(pEmail)) Then
            ObterIdUsuario = CLng(dr.Cells(i, 1).Value): Exit Function
        End If
    Next i
    ObterIdUsuario = 0: Exit Function
ErrHandler:
    ObterIdUsuario = 0
End Function

Public Function CarregarEmailsAtivos() As String()
    Dim ws As Worksheet, tb As ListObject, dr As Range
    Dim i As Long, n As Long, em() As String
    On Error GoTo ErrHandler
    Set ws = ThisWorkbook.Worksheets("dUsuarios")
    Set tb = ws.ListObjects("dUsuario")
    If tb.DataBodyRange Is Nothing Then CarregarEmailsAtivos = em: Exit Function
    Set dr = tb.DataBodyRange: n = 0
    For i = 1 To dr.Rows.Count
        If dr.Cells(i, 3).Value = 1 Then n = n + 1
    Next i
    If n = 0 Then CarregarEmailsAtivos = em: Exit Function
    ReDim em(1 To n): n = 0
    For i = 1 To dr.Rows.Count
        If dr.Cells(i, 3).Value = 1 Then n = n + 1: em(n) = dr.Cells(i, 2).Value
    Next i
    CarregarEmailsAtivos = em
ErrHandler:
End Function

Public Sub ResetarSessao()
    UsuarioAtual = 0
    EmailAtual = ""
End Sub
