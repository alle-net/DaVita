Attribute VB_Name = "modDebug"
Option Explicit

' Executar do VBA (F5 ou F8) para reiniciar sem fechar o Excel
Sub Reset()
    On Error Resume Next
    Unload frmPrincipal
    Unload frmLogin
    On Error GoTo 0
    
    modAutenticacao.ResetarSessao
    frmLogin.Show vbModal
    
    If modAutenticacao.UsuarioAtual > 0 Then
        frmPrincipal.Show vbModeless
    End If
End Sub
