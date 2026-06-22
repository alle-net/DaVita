VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmPrincipal 
   Caption         =   "Principal"
   ClientHeight    =   10000
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   20000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "frmPrincipal"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private Sub UserForm_Initialize()
    Me.Caption = "Controle Financeiro"
    Me.StartUpPosition = 0
    Centralizar
End Sub

Private Sub Centralizar()
    Me.Left = (Application.Width - Me.Width) / 2
    Me.Top = (Application.Height - Me.Height) / 2
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    If CloseMode = 0 Then
        If MsgBox("Deseja realmente sair do sistema?", vbQuestion + vbYesNo, "Sair") = vbNo Then
            Cancel = True
        Else
            modAutenticacao.ResetarSessao
        End If
    End If
End Sub
