Attribute VB_Name = "modDados"
Option Explicit

Public Const PAGE_SIZE As Long = 25

Private mAllData() As Variant
Private mDisplayData() As Variant
Private mTotalRecords As Long
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
    Set tb = ws.ListObjects("Dados")
    
    If tb.DataBodyRange Is Nothing Then
        mTotalRecords = 0: mCurrentPage = 1: mTotalPages = 1
        ReDim mAllData(1 To 1, 1 To 16)
        mDisplayData = mAllData
        CarregarDadosUsuario = True: Exit Function
    End If
    
    Dim rawData As Variant
    rawData = tb.DataBodyRange.Value
    n = 0
    For i = 1 To UBound(rawData, 1)
        If rawData(i, 2) = usuarioID Then n = n + 1
    Next i
    
    If n = 0 Then
        mTotalRecords = 0: mCurrentPage = 1: mTotalPages = 1
        ReDim mAllData(1 To 1, 1 To 16)
        mDisplayData = mAllData
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
    
    mTotalRecords = n: mCurrentPage = 1
    mTotalPages = ((n - 1) \ PAGE_SIZE) + 1
    CarregarMapasDimensoes
    mDisplayData = FormatarParaExibicao(mAllData)
    CarregarDadosUsuario = True: Exit Function
ErrHandler:
    CarregarDadosUsuario = False
End Function

Private Sub CarregarMapasDimensoes()
    mUsuariosDim = CarregarDimensao("Usuarios", "Usuarios")
    mHospitaisDim = CarregarDimensao("Hospitais", "Hospitais")
    mRegionaisDim = CarregarDimensao("Regionais", "Regionais")
    mUnidadesDim = CarregarDimensao("Unidades", "Unidades")
    mStatusDim = CarregarDimensao("StatusNFe", "StatusNFe")
    mMotivosDim = CarregarDimensao("MotivosGlosa", "MotivosGlosa")
End Sub

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

Public Function GetPageData() As Variant
    Dim si As Long, ei As Long, i As Long, j As Long, n As Long
    Dim r() As Variant
    
    If mTotalRecords = 0 Then
        GetPageData = Array(): Exit Function
    End If
    
    si = (mCurrentPage - 1) * PAGE_SIZE + 1
    ei = si + PAGE_SIZE - 1
    If ei > mTotalRecords Then ei = mTotalRecords
    
    n = ei - si + 1: ReDim r(0 To n - 1, 0 To 15)
    For i = si To ei
        j = i - si
        r(j, 0) = mAllData(i, 1): r(j, 1) = mAllData(i, 2)
        r(j, 2) = mAllData(i, 3): r(j, 3) = mAllData(i, 4)
        r(j, 4) = mAllData(i, 5): r(j, 5) = mAllData(i, 6)
        r(j, 6) = mAllData(i, 7): r(j, 7) = mAllData(i, 8)
        r(j, 8) = mAllData(i, 9): r(j, 9) = mAllData(i, 10)
        r(j, 10) = mAllData(i, 11): r(j, 11) = mAllData(i, 12)
        r(j, 12) = mAllData(i, 13): r(j, 13) = mAllData(i, 14)
        r(j, 14) = mAllData(i, 15): r(j, 15) = mAllData(i, 16)
    Next i
    GetPageData = r
End Function

Public Function GetPageDataFormatado() As Variant
    Dim si As Long, ei As Long, i As Long, j As Long, n As Long
    Dim r() As Variant
    
    If mTotalRecords = 0 Then
        GetPageDataFormatado = Array(): Exit Function
    End If
    
    si = (mCurrentPage - 1) * PAGE_SIZE + 1
    ei = si + PAGE_SIZE - 1
    If ei > mTotalRecords Then ei = mTotalRecords
    
    n = ei - si + 1: ReDim r(0 To n - 1, 0 To 15)
    For i = si To ei
        j = i - si
        r(j, 0) = mDisplayData(i, 1): r(j, 1) = mDisplayData(i, 2)
        r(j, 2) = mDisplayData(i, 3): r(j, 3) = mDisplayData(i, 4)
        r(j, 4) = mDisplayData(i, 5): r(j, 5) = mDisplayData(i, 6)
        r(j, 6) = mDisplayData(i, 7): r(j, 7) = mDisplayData(i, 8)
        r(j, 8) = mDisplayData(i, 9): r(j, 9) = mDisplayData(i, 10)
        r(j, 10) = mDisplayData(i, 11): r(j, 11) = mDisplayData(i, 12)
        r(j, 12) = mDisplayData(i, 13): r(j, 13) = mDisplayData(i, 14)
        r(j, 14) = mDisplayData(i, 15): r(j, 15) = mDisplayData(i, 16)
    Next i
    GetPageDataFormatado = r
End Function

Public Function GetPageInfo() As String
    GetPageInfo = "Pagina " & mCurrentPage & " de " & mTotalPages & _
                  " (" & mTotalRecords & " registros)"
End Function

Public Function GetRecordIdxAtGridRow(gridRow As Long) As Long
    GetRecordIdxAtGridRow = (mCurrentPage - 1) * PAGE_SIZE + gridRow
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
Public Function GetTotalRecords() As Long: GetTotalRecords = mTotalRecords: End Function

Public Function GetRecordByGlobalIdx(idx As Long) As Variant
    Dim r(1 To 16) As Variant
    If idx >= 1 And idx <= mTotalRecords Then
        Dim c As Long
        For c = 1 To 16: r(c) = mAllData(idx, c): Next
    End If
    GetRecordByGlobalIdx = r
End Function

Public Function CarregarDimensao(aba As String, tabela As String) As Variant
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

Private Function GerarGUID() As String
    Dim g As Object
    Set g = CreateObject("Scriptlet.TypeLib")
    GerarGUID = Left(g.Guid, 38)
End Function

Public Function AdicionarRegistro(valores As Variant) As Boolean
    Dim ws As Worksheet, tb As ListObject, nr As ListRow
    Dim c As Long
    
    On Error GoTo ErrHandler
    Set ws = ThisWorkbook.Worksheets("Dados")
    Set tb = ws.ListObjects("Dados")
    
    Set nr = tb.ListRows.Add
    ' Gerar ID curto a partir do GUID e garantir unicidade
    Dim newId As String, attempt As Long
    For attempt = 1 To 5
        newId = GerarGUIDShort()
        If tb.DataBodyRange Is Nothing Then Exit For
        If tb.ListColumns(1).DataBodyRange.Find(newId, , , xlWhole) Is Nothing Then Exit For
    Next attempt
    nr.Range.Cells(1, 1).Value = newId
    For c = 2 To 16
        nr.Range.Cells(1, c).Value = valores(c)
    Next c
    AdicionarRegistro = True: Exit Function
ErrHandler:
    AdicionarRegistro = False
End Function

' === ID curto (Base62) helpers ===
Private Function GerarGUIDShort() As String
    Dim g As String
    g = GerarGUID
    g = Replace(g, "{", ""): g = Replace(g, "}", ""): g = Replace(g, "-", "")
    Dim b() As Byte
    b = HexStringToBytes(g)
    GerarGUIDShort = Base62Encode(b)
    If Len(GerarGUIDShort) > 22 Then GerarGUIDShort = Left(GerarGUIDShort, 22)
End Function

Private Function HexStringToBytes(hexStr As String) As Byte()
    Dim n As Long, i As Long, b() As Byte
    n = Len(hexStr) \ 2
    ReDim b(0 To n - 1)
    For i = 0 To n - 1
        b(i) = CLng("&H" & Mid$(hexStr, i * 2 + 1, 2))
    Next i
    HexStringToBytes = b
End Function

Private Function Base62Encode(bytes() As Byte) As String
    Dim alphabet As String: alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    Dim arr() As Byte, i As Long, j As Long
    arr = bytes
    Dim result As String: result = ""
    Dim nonZero As Boolean

    Do
        nonZero = False
        Dim carry As Long: carry = 0
        For i = LBound(arr) To UBound(arr)
            Dim val As Long
            val = carry * 256 + arr(i)
            arr(i) = (val \ 62) And 255
            carry = val Mod 62
            If arr(i) <> 0 Then nonZero = True
        Next i
        result = Mid$(alphabet, carry + 1, 1) & result
        ' Trim leading zeros
        Dim firstNonZero As Long: firstNonZero = LBound(arr)
        Do While firstNonZero <= UBound(arr) And arr(firstNonZero) = 0
            firstNonZero = firstNonZero + 1
        Loop
        If firstNonZero > LBound(arr) Then
            If firstNonZero > UBound(arr) Then
                ReDim arr(0 To 0): arr(0) = 0
            Else
                Dim tmp() As Byte
                ReDim tmp(0 To UBound(arr) - firstNonZero)
                For j = firstNonZero To UBound(arr)
                    tmp(j - firstNonZero) = arr(j)
                Next j
                arr = tmp
            End If
        End If
        If UBound(arr) = 0 And arr(0) = 0 Then Exit Do
    Loop While True

    If result = "" Then result = "0"
    Base62Encode = result
End Function

Public Function EditarRegistro(pID As String, valores As Variant) As Boolean
    Dim ws As Worksheet, tb As ListObject, f As Range, c As Long
    On Error GoTo ErrHandler
    Set ws = ThisWorkbook.Worksheets("Dados")
    Set tb = ws.ListObjects("Dados")
    If tb.DataBodyRange Is Nothing Then EditarRegistro = False: Exit Function
    Set f = tb.ListColumns(1).DataBodyRange.Find(pID, , , xlWhole)
    If f Is Nothing Then EditarRegistro = False: Exit Function
    For c = 2 To 16
        f.Offset(0, c - 1).Value = valores(c)
    Next c
    EditarRegistro = True: Exit Function
ErrHandler:
    EditarRegistro = False
End Function

Public Function ExcluirRegistro(pID As String) As Boolean
    Dim ws As Worksheet, tb As ListObject, f As Range
    On Error GoTo ErrHandler
    Set ws = ThisWorkbook.Worksheets("Dados")
    Set tb = ws.ListObjects("Dados")
    If tb.DataBodyRange Is Nothing Then ExcluirRegistro = False: Exit Function
    Set f = tb.ListColumns(1).DataBodyRange.Find(pID, , , xlWhole)
    If f Is Nothing Then ExcluirRegistro = False: Exit Function
    f.EntireRow.Delete
    ExcluirRegistro = True: Exit Function
ErrHandler:
    ExcluirRegistro = False
End Function

Private Function FormatarParaExibicao(arr As Variant) As Variant
    Dim r As Long, c As Long, i As Long, j As Long
    Dim fmt(1 To 16) As String
    
    ' === Definição de formatos por coluna para exibição no ListBox ===
    fmt(1) = ""                ' ID (GUID)
    fmt(2) = ""                ' IdUsuario
    fmt(3) = "mmm/aaaa"        ' Competencia
    fmt(4) = ""                ' IdHospital
    fmt(5) = ""                ' IdRegional
    fmt(6) = ""                ' IdUnidade
    fmt(7) = ""                ' Titulo
    fmt(8) = ""                ' NFe
    fmt(9) = ""                ' IdStatus
    fmt(10) = ""               ' IdMotivo
    fmt(11) = "dd/mm/yyyy"     ' EnvioNFe
    fmt(12) = "R$ #,##0.00"    ' ValorFaturamento
    fmt(13) = "R$ #,##0.00"    ' ValorPerda
    fmt(14) = "R$ #,##0.00"    ' ValorGlosa
    fmt(15) = ""               ' Observacao
    fmt(16) = "dd/mm/yyyy hh:mm"  ' Data
    
    r = UBound(arr, 1): c = UBound(arr, 2)
    ReDim outArr(1 To r, 1 To c)
    
    For i = 1 To r
        For j = 1 To c
            Select Case j
                Case 2
                    outArr(i, j) = ObterDescricaoDimensao(arr(i, j), mUsuariosDim)
                    If outArr(i, j) = "" Then outArr(i, j) = arr(i, j)
                Case 4
                    outArr(i, j) = ObterDescricaoDimensao(arr(i, j), mHospitaisDim)
                    If outArr(i, j) = "" Then outArr(i, j) = arr(i, j)
                Case 5
                    outArr(i, j) = ObterDescricaoDimensao(arr(i, j), mRegionaisDim)
                    If outArr(i, j) = "" Then outArr(i, j) = arr(i, j)
                Case 6
                    outArr(i, j) = ObterDescricaoDimensao(arr(i, j), mUnidadesDim)
                    If outArr(i, j) = "" Then outArr(i, j) = arr(i, j)
                Case 9
                    outArr(i, j) = ObterDescricaoDimensao(arr(i, j), mStatusDim)
                    If outArr(i, j) = "" Then outArr(i, j) = arr(i, j)
                Case 10
                    outArr(i, j) = ObterDescricaoDimensao(arr(i, j), mMotivosDim)
                    If outArr(i, j) = "" Then outArr(i, j) = arr(i, j)
                Case Else
                    If j >= LBound(fmt) And j <= UBound(fmt) Then
                        If fmt(j) <> "" And Not IsError(arr(i, j)) And Not IsEmpty(arr(i, j)) Then
                            outArr(i, j) = Format$(arr(i, j), fmt(j))
                        Else
                            outArr(i, j) = arr(i, j)
                        End If
                    Else
                        outArr(i, j) = arr(i, j)
                    End If
            End Select
        Next j
    Next i
    FormatarParaExibicao = outArr
End Function

Private Function ValorSeguro(v As Variant) As Variant
    If IsError(v) Then ValorSeguro = "" Else ValorSeguro = v
End Function

Public Sub TestarConexao()
    Dim msg As String: msg = ""
    Dim ws As Worksheet, tb As ListObject, dr As Range
    Dim i As Long, email As String
    
    On Error Resume Next
    
    ' Teste 1: Aba Usuarios
    Set ws = ThisWorkbook.Worksheets("Usuarios")
    If ws Is Nothing Then
        msg = msg & "[ERRO] Aba Usuarios nao encontrada!" & vbCrLf
    Else
        msg = msg & "[OK] Aba Usuarios encontrada" & vbCrLf
        Set tb = ws.ListObjects("Usuarios")
        If tb Is Nothing Then
            msg = msg & "[ERRO] Tabela 'Usuarios' nao encontrada na aba Usuarios" & vbCrLf
        ElseIf tb.DataBodyRange Is Nothing Then
            msg = msg & "[AVISO] Tabela Usuarios sem dados" & vbCrLf
        Else
            Set dr = tb.DataBodyRange
            msg = msg & "[OK] Usuarios: " & dr.Rows.Count & " registros" & vbCrLf
            msg = msg & "  Col1(ID) | Col2(Email) | Col3(Status)" & vbCrLf
            For i = 1 To Application.WorksheetFunction.Min(dr.Rows.Count, 10)
                msg = msg & "  " & dr.Cells(i, 1).Value & " | " & dr.Cells(i, 2).Value & " | " & dr.Cells(i, 3).Value & vbCrLf
            Next i
        End If
    End If
    
    ' Teste 2: Aba Dados
    Set ws = ThisWorkbook.Worksheets("Dados")
    If ws Is Nothing Then
        msg = msg & "[ERRO] Aba Dados nao encontrada!" & vbCrLf
    Else
        msg = msg & "[OK] Aba Dados encontrada" & vbCrLf
        Set tb = ws.ListObjects("Dados")
        If tb Is Nothing Then
            msg = msg & "[ERRO] Tabela 'Dados' nao encontrada" & vbCrLf
        ElseIf tb.DataBodyRange Is Nothing Then
            msg = msg & "[AVISO] Tabela Dados sem dados" & vbCrLf
        Else
            Set dr = tb.DataBodyRange
            msg = msg & "[OK] Dados: " & dr.Rows.Count & " registros, " & dr.Columns.Count & " colunas" & vbCrLf
            msg = msg & "  Col2(IdUsuario) valores (5 primeiros):" & vbCrLf
            For i = 1 To Application.WorksheetFunction.Min(dr.Rows.Count, 5)
                msg = msg & "  Linha " & i & ": " & dr.Cells(i, 2).Value & vbCrLf
            Next i
        End If
    End If
    
    ' Teste 3: ObterIdUsuario
    msg = msg & vbCrLf & "--- Teste ObterIdUsuario ---" & vbCrLf
    email = modAutenticacao.EmailAtual
    msg = msg & "EmailAtual = '" & email & "'" & vbCrLf
    msg = msg & "UsuarioAtual = " & modAutenticacao.UsuarioAtual & vbCrLf
    If email <> "" Then
        msg = msg & "ObterIdUsuario('" & email & "') = " & modAutenticacao.ObterIdUsuario(email) & vbCrLf
    End If
    
    MsgBox msg, vbInformation, "Diagnostico Completo"
End Sub
