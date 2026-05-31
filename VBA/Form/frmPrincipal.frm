VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmPrincipal 
   Caption         =   "Registros"
   ClientHeight    =   11730
   ClientLeft      =   120
   ClientTop       =   465
   ClientWidth     =   24615
   OleObjectBlob   =   "frmPrincipal.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "frmPrincipal"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private Sub UserForm_Initialize()
    lblTitulo.ForeColor = RGB(0, 118, 182)
    lblTitulo.Font.Size = 18
    lblTitulo.Font.Bold = True
    lblUsuarioLogado.Caption = "Usuario: " & modAutenticacao.EmailAtual
    lblTituloFat.ForeColor = RGB(0, 118, 182)
    lblTituloGlosa.ForeColor = RGB(0, 118, 182)
    lblTituloPerda.ForeColor = RGB(0, 118, 182)
    lblFaturamento.ForeColor = RGB(0, 118, 182)
    lblFaturamento.Font.Bold = True
    lblGlosa.ForeColor = RGB(0, 118, 182)
    lblGlosa.Font.Bold = True
    lblPerda.ForeColor = RGB(0, 118, 182)
    lblPerda.Font.Bold = True
    
    If modDados.CarregarDadosUsuario(modAutenticacao.UsuarioAtual) Then
        PreencherGrid
        AtualizarNavegacao
        AtualizarSubtotais
    End If
End Sub
Private Sub PreencherGrid()
    Dim dados As Variant
    dados = modDados.GetPageDataFormatado
    With lstDados
        .Clear
        If Not IsArray(dados) Then Exit Sub
        If UBound(dados, 1) < 0 Then Exit Sub
        .ColumnCount = 13
        .ColumnWidths = "65;100;100;100;100;60;80;80;100;80;80;80;100"
        .List = dados
    End With
End Sub

Private Sub AtualizarNavegacao()
    lblPagina.Caption = modDados.GetPageInfo
    cmdAnterior.Enabled = (modDados.GetCurrentPage > 1)
    cmdProximo.Enabled = (modDados.GetCurrentPage < modDados.GetTotalPages)
End Sub

Private Sub AtualizarSubtotais()
    Dim fat As Double, perda As Double, glosa As Double
    modDados.CalcularSubtotais fat, perda, glosa
    lblFaturamento.Caption = "R$ " & Format$(fat, "#,##0.00")
    lblGlosa.Caption = "R$ " & Format$(glosa, "#,##0.00")
    lblPerda.Caption = "R$ " & Format$(perda, "#,##0.00")
End Sub

Private Sub txtBoxFiltro_Change()
    modDados.AplicarFiltro txtBoxFiltro.Value
    PreencherGrid
    AtualizarNavegacao
    AtualizarSubtotais
End Sub

Private Sub cmdAnterior_Click()
    modDados.PreviousPage
    PreencherGrid
    AtualizarNavegacao
End Sub

Private Sub cmdProximo_Click()
    modDados.NextPage
    PreencherGrid
    AtualizarNavegacao
End Sub

Private Sub cmdAtualizar_Click()
    If modDados.CarregarDadosUsuario(modAutenticacao.UsuarioAtual) Then
        txtBoxFiltro.Value = ""
        PreencherGrid
        AtualizarNavegacao
        AtualizarSubtotais
    End If
End Sub

Private Sub cmdAdd_Click()
    MsgBox "Implementar frmEdicao (Add)", vbInformation, "Adicionar"
End Sub

Private Sub cmdEditar_Click()
    If lstDados.ListIndex = -1 Then
        MsgBox "Selecione um registro.", vbExclamation, "Editar"
        Exit Sub
    End If
    MsgBox "Implementar frmEdicao (Edit)", vbInformation, "Editar"
End Sub

Private Sub cmdExcluir_Click()
    If lstDados.ListIndex = -1 Then
        MsgBox "Selecione um registro.", vbExclamation, "Excluir"
        Exit Sub
    End If
    If MsgBox("Deseja excluir este registro?", vbQuestion + vbYesNo, "Excluir") = vbYes Then
        MsgBox "Implementar exclusao", vbInformation, "Excluir"
    End If
End Sub

Private Sub UserForm_QueryClose(Cancel As Integer, CloseMode As Integer)
    If CloseMode = 0 Then
        modAutenticacao.ResetarSessao
        Unload Me
    End If
End Sub

