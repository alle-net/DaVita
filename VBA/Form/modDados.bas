Attribute VB_Name = "modDados"
Option Explicit

Public Const PAGE_SIZE As Long = 25

Private mAllData() As Variant
Private mAllDataSearchable() As String
Private mFilteredIdx() As Long
Private mTotalRecords As Long
Private mTotalFiltered As Long
Private mCurrentPage As Long
Private mTotalPages As Long

Private mUsuariosDim As Variant
Private mHospitaisDim As Variant
Private mRegionaisDim As Variant
Private mUnidadesDim As Variant
Private mStatusDim As Variant
Private mMotivosDim As Variant

Public Function CarregarDadosUsuario(usuarioID As Long) As Boolean
    Dim ws As Worksheet, tb As ListObject, dr As Range
    Dim i As Long, n As Long
    
    On Error GoTo ErrHandler
    Set ws = ThisWorkbook.Worksheets("Dados")
    Set tb = ws.ListObjects("TabDados")
    
    If tb.DataBodyRange Is Nothing Then
        mTotalRecords = 0: mTotalFiltered = 0
        mCurrentPage = 1: mTotalPages = 1
        ReDim mAllData(1 To 1, 1 To 16)
        CarregarDadosUsuario = True: Exit Function
    End If
    
    Dim rawData As Variant
    rawData = tb.DataBodyRange.Value
    n = 0
    For i = 1 To UBound(rawData, 1)
        If rawData(i, 2) = usuarioID Then n = n + 1
    Next i
    
    If n = 0 Then
        mTotalRecords = 0: mTotalFiltered = 0
        mCurrentPage = 1: mTotalPages = 1
        ReDim mAllData(1 To 1, 1 To 16)
        CarregarDadosUsuario = True: Exit Function
    End If
    
    ReDim mAllData(1 To n, 1 To 16): n = 0
    For i = 1 To UBound(rawData, 1)
        If rawData(i, 2) = usuarioID Then
            n = n + 1
            Dim c As Long
            For c = 1 To 16
                mAllData(n, c) = ValorSeguro(rawData(i, c))
            Next c
        End If
    Next i
    
    mTotalRecords = n
    ReDim mFilteredIdx(1 To n)
    For i = 1 To n: mFilteredIdx(i) = i: Next i
    mTotalFiltered = n
    
    mCurrentPage = 1
    mTotalPages = ((n - 1) \ PAGE_SIZE) + 1
    
    CarregarMapasDimensoes
    ReDim mAllDataSearchable(1 To n)
    For i = 1 To n
        mAllDataSearchable(i) = LCase(ResolveSearchText(i))
    Next i
    CarregarDadosUsuario = True: Exit Function
ErrHandler:
    CarregarDadosUsuario = False
End Function

Public Sub AplicarFiltro(texto As String)
    Dim i As Long, j As Long, n As Long, txt As String
    txt = LCase(Trim(texto))
    
    If txt = "" Then
        ReDim mFilteredIdx(1 To mTotalRecords)
        For i = 1 To mTotalRecords: mFilteredIdx(i) = i: Next i
        mTotalFiltered = mTotalRecords
    Else
        n = 0
        ReDim mFilteredIdx(1 To mTotalRecords)
        For i = 1 To mTotalRecords
            If InStr(mAllDataSearchable(i), txt) > 0 Then
                n = n + 1
                mFilteredIdx(n) = i
            End If
        Next i
        If n = 0 Then
            mTotalFiltered = 0: ReDim mFilteredIdx(1 To 1)
        Else
            ReDim Preserve mFilteredIdx(1 To n)
            mTotalFiltered = n
        End If
    End If
    
    mCurrentPage = 1
    If mTotalFiltered = 0 Then mTotalPages = 1 Else mTotalPages = ((mTotalFiltered - 1) \ PAGE_SIZE) + 1
End Sub

Public Function GetPageData() As Variant
    Dim si As Long, ei As Long, i As Long, j As Long, n As Long
    Dim r() As Variant, idx As Long
    
    If mTotalFiltered = 0 Then
        GetPageData = Array(): Exit Function
    End If
    
    si = (mCurrentPage - 1) * PAGE_SIZE + 1
    ei = si + PAGE_SIZE - 1
    If ei > mTotalFiltered Then ei = mTotalFiltered
    
    n = ei - si + 1: ReDim r(0 To n - 1, 0 To 15)
    For i = si To ei
        idx = mFilteredIdx(i): j = i - si
        Dim c2 As Long
        For c2 = 1 To 16
            r(j, c2 - 1) = mAllData(idx, c2)
        Next c2
    Next i
    GetPageData = r
End Function

Public Function GetPageDataFormatado() As Variant
    Dim raw As Variant
    raw = GetPageData()
    If Not IsArray(raw) Then
        GetPageDataFormatado = raw
        Exit Function
    End If
    
    Dim n As Long, i As Long
    On Error Resume Next
    n = UBound(raw, 1) + 1
    On Error GoTo 0
    If n = 0 Then
        GetPageDataFormatado = Array()
        Exit Function
    End If
    Dim res() As Variant
    ReDim res(0 To n - 1, 0 To 12)
    
    Dim tmp As String, v As Variant
    For i = 0 To n - 1
        ' 0: Competencia (raw col 3)
        v = raw(i, 2)
        If IsDate(v) Then
            tmp = Format$(v, "mmm/yyyy")
            res(i, 0) = UCase(Left$(tmp, 1)) & Mid$(tmp, 2)
        ElseIf IsNumeric(v) Then
            tmp = Format$(CDate(v), "mmm/yyyy")
            res(i, 0) = UCase(Left$(tmp, 1)) & Mid$(tmp, 2)
        Else
            res(i, 0) = v
        End If
        
        ' 1: Regional (raw col 5)
        res(i, 1) = ObterDescricaoDimensao(raw(i, 4), mRegionaisDim)
        
        ' 2: Unidade (raw col 6)
        res(i, 2) = ObterDescricaoDimensao(raw(i, 5), mUnidadesDim)
        
        ' 3: Hospital (raw col 4)
        res(i, 3) = ObterDescricaoDimensao(raw(i, 3), mHospitaisDim)
        
        ' 4: Titulo (raw col 7)
        res(i, 4) = raw(i, 6)
        
        ' 5: NFe (raw col 8)
        res(i, 5) = raw(i, 7)
        
        ' 6: StatusNFe (raw col 9)
        res(i, 6) = ObterDescricaoDimensao(raw(i, 8), mStatusDim)
        
        ' 7: DataEnvioNFe (raw col 11)
        v = raw(i, 10)
        If IsDate(v) Then
            res(i, 7) = Format$(v, "dd/mm/yyyy")
        ElseIf IsNumeric(v) Then
            res(i, 7) = Format$(CDate(v), "dd/mm/yyyy")
        Else
            res(i, 7) = v
        End If
        
        ' 8: MotivoGlosa (raw col 10)
        res(i, 8) = ObterDescricaoDimensao(raw(i, 9), mMotivosDim)
        
        ' 9: ValorFaturamento (raw col 12)
        v = raw(i, 11)
        If IsNumeric(v) Then res(i, 9) = Format$(CDbl(v), "#,##0.00") Else res(i, 9) = v
        
        ' 10: ValorGlosa (raw col 14)
        v = raw(i, 13)
        If IsNumeric(v) Then res(i, 10) = Format$(CDbl(v), "#,##0.00") Else res(i, 10) = v
        
        ' 11: ValorPerda (raw col 13)
        v = raw(i, 12)
        If IsNumeric(v) Then res(i, 11) = Format$(CDbl(v), "#,##0.00") Else res(i, 11) = v
        
        ' 12: Observacao (raw col 15) - limitada a 80 caracteres
        res(i, 12) = Left$(raw(i, 14), 80)
    Next i
    GetPageDataFormatado = res
End Function

Public Function GetPageInfo() As String
    If mTotalFiltered = 0 Then
        GetPageInfo = "Pagina 0 de 0 (0 registros)"
    Else
        GetPageInfo = "Pagina " & mCurrentPage & " de " & mTotalPages & _
                      " (" & mTotalFiltered & " registros)"
    End If
End Function

Public Sub GoToPage(p As Long)
    If p >= 1 And p <= mTotalPages Then mCurrentPage = p
End Sub

Public Sub NextPage()
    If mCurrentPage < mTotalPages Then mCurrentPage = mCurrentPage + 1
End Sub

Public Sub PreviousPage()
    If mCurrentPage > 1 Then mCurrentPage = mCurrentPage - 1
End Sub

Public Function GetCurrentPage() As Long: GetCurrentPage = mCurrentPage: End Function
Public Function GetTotalPages() As Long: GetTotalPages = mTotalPages: End Function
Public Function GetTotalFiltered() As Long: GetTotalFiltered = mTotalFiltered: End Function

Public Sub CalcularSubtotais(ByRef pFat As Double, ByRef pPerda As Double, ByRef pGlosa As Double)
    Dim i As Long, idx As Long
    pFat = 0: pPerda = 0: pGlosa = 0
    For i = 1 To mTotalFiltered
        idx = mFilteredIdx(i)
        If IsNumeric(mAllData(idx, 12)) Then pFat = pFat + CDbl(mAllData(idx, 12))
        If IsNumeric(mAllData(idx, 13)) Then pPerda = pPerda + CDbl(mAllData(idx, 13))
        If IsNumeric(mAllData(idx, 14)) Then pGlosa = pGlosa + CDbl(mAllData(idx, 14))
    Next i
End Sub

Private Sub CarregarMapasDimensoes()
    mUsuariosDim = CarregarDimensao("dUsuarios", "dUsuario")
    mHospitaisDim = CarregarDimensao("dHospital", "dHospitais")
    mRegionaisDim = CarregarDimensao("dRegional", "dRegionais")
    mUnidadesDim = CarregarDimensao("dUnidades", "dUnidade")
    mStatusDim = CarregarDimensao("dStatusNFe", "dStatusNFEs")
    mMotivosDim = CarregarDimensao("dMotivosGlosas", "dMotivosGlosa")
End Sub

Private Function CarregarDimensao(aba As String, tabela As String) As Variant
    Dim ws As Worksheet, tb As ListObject, dr As Range
    Dim i As Long, n As Long, res() As Variant
    On Error GoTo ErrHandler
    Set ws = ThisWorkbook.Worksheets(aba)
    Set tb = ws.ListObjects(tabela)
    If tb.DataBodyRange Is Nothing Then GoTo ErrHandler
    Set dr = tb.DataBodyRange: n = 0
    For i = 1 To dr.Rows.Count
        If dr.Cells(i, 3).Value = 1 Then n = n + 1
    Next i
    If n = 0 Then GoTo ErrHandler
    ReDim res(1 To n, 1 To 2): n = 0
    For i = 1 To dr.Rows.Count
        If dr.Cells(i, 3).Value = 1 Then
            n = n + 1
            res(n, 1) = dr.Cells(i, 1).Value
            res(n, 2) = dr.Cells(i, 2).Value
        End If
    Next i
    CarregarDimensao = res
    Exit Function
ErrHandler:
    CarregarDimensao = Array()
End Function

Private Function ObterDescricaoDimensao(id As Variant, mapa As Variant) As Variant
    Dim i As Long
    If IsEmpty(id) Or IsNull(id) Then Exit Function
    If Not IsArray(mapa) Then Exit Function
    On Error Resume Next
    For i = LBound(mapa, 1) To UBound(mapa, 1)
        If CStr(mapa(i, 1)) = CStr(id) Then
            ObterDescricaoDimensao = mapa(i, 2)
            Exit Function
        End If
    Next i
    On Error GoTo 0
End Function

Private Function ResolveSearchText(rowIdx As Long) As String
    Dim parts(1 To 16) As String, v As Variant, c As Long
    For c = 1 To 16
        v = mAllData(rowIdx, c)
        Dim tmp As String
        Select Case c
            Case 3:  If IsDate(v) Then tmp = Format$(v, "mmm/yyyy"): parts(c) = UCase(Left$(tmp, 1)) & Mid$(tmp, 2) Else parts(c) = v
            Case 4:  parts(c) = ObterDescricaoDimensao(v, mHospitaisDim)
            Case 5:  parts(c) = ObterDescricaoDimensao(v, mRegionaisDim)
            Case 6:  parts(c) = ObterDescricaoDimensao(v, mUnidadesDim)
            Case 9:  parts(c) = ObterDescricaoDimensao(v, mStatusDim)
            Case 10: parts(c) = ObterDescricaoDimensao(v, mMotivosDim)
            Case 11: If IsDate(v) Then parts(c) = Format$(v, "dd/mm/yyyy") Else parts(c) = v
            Case 12, 13, 14: If IsNumeric(v) Then parts(c) = Format$(CDbl(v), "0.00") Else parts(c) = v
            Case Else: parts(c) = v
        End Select
    Next c
    ResolveSearchText = Join(parts, " ")
End Function

Private Function ValorSeguro(v As Variant) As Variant
    If IsError(v) Then ValorSeguro = "" Else ValorSeguro = v
End Function
