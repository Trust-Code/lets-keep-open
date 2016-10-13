## -*- coding: utf-8 -*-
<html>
<head>
    <style type="text/css">
        ${css}
        .datagrid { border-collapse: collapse; text-align: left; width: 100%; }
        .datagrid {font: normal 12px/150% Arial, Helvetica, sans-serif; background: #fff; overflow: hidden; border: 1px solid #006699; -webkit-border-radius: 3px; -moz-border-radius: 3px; border-radius: 3px; }
        .datagrid td, .datagrid table th { padding: 2px 5px; }
        .datagrid thead th { background-color:#006699; color:#FFFFFF; font-size: 15px; font-weight: bold; border-left: 1px solid #0070A8; text-align:center; }
        .datagrid thead th:first-child { border: none; }
        .datagrid tbody td { color: #000; border-left: 1px solid #E1EEF4;font-size: 12px;font-weight: normal; }
        .datagrid tbody .alt td { background: #E1EEF4; color: #000; }
        .datagrid tbody td:first-child { border-left: none; }
        .datagrid tr.enfase { background-color:#006699; }
        .datagrid tr.enfase td { color:#FFFFFF; font-size: 15px;  }
    </style>
</head>
<body>
    <%page expression_filter="entity"/>
    <%
    def carriage_returns(text):
        return text.replace('\n', '<br />')
    %>

    %for partner in objects:
    <% setLang(partner.lang) %>

    <div style="padding-top:10px;">
    Período de recebimento das mensalidades: ${data['formatted_start_date']} a ${data['formatted_end_date']}
    </div>

    <div style="padding-top:10px; padding-bottom:10px;">
        <label><b>CNPJ:</b> ${partner.cnpj_cpf or ''} </label><br />
        <label><b>Comissionada:</b> ${partner.legal_name or ''} </label>
    </div>

    <%
    comissoes, bruto, impostos, liquido = partner.get_commission(data['start_date'], data['end_date'])
    contador = 0
    %>
    <table class="datagrid" width="100%">
        <thead>
            <tr>
                <th style="width:130px;">Produto</th>
                <th style="width:125px;">Cnpj</th>
                <th>Cliente TEF2</th>
                <th>Vencimento</th>
                <th>Pagamento</th>
                <th>Mensalidade</th>
                <th style="width:30px;">%</th>
                <th style="width:80px;">Valor</th>
            </tr>
        </thead>
        <tbody>
            %for comissao in comissoes:
            % if contador%2 == 0:
                <tr>
            % else:
                <tr class="alt">
            % endif
                <td style="max-width: 100px; overflow:hidden; text-overflow: ellipsis; white-space: nowrap;">${comissao['produto']}</td>
                <td style="text-align:center;">${comissao['cnpj']}</td>
                <td style="max-width: 280px; overflow:hidden; text-overflow: ellipsis; white-space: nowrap;">${comissao['cliente']}</td>
                <td style="text-align:center;">${comissao['vencimento']}</td>
                <td style="text-align:center;">${comissao['pagamento']}</td>
                <td style="text-align:right;">${comissao['mensalidade']}</td>
                <td style="text-align:right;">${comissao['percentual']}</td>
                <td style="text-align:right;">${comissao['valor']}</td>
            </tr>
            <%
                contador += 1
            %>
            %endfor
        </tbody>
    </table>


    <div style="margin-top:20px;">
        <div style="float:right; width:50%;">
            <hr />
            <strong>* Total Bruto: R$ </strong><label style="float:right;">${bruto}</label>
            <hr />
            <table class="datagrid" width="100%">
                <thead>
                    <tr>
                        <th colspan="3">Impostos retidos - Prefeitura de São Paulo</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="alt">
                        <td style="font-weight:bold;">ISS</td>
                        <td style="text-align:center;">${impostos['perc_iss']}%</td>
                        <td style="text-align:right;">R$ ${impostos['iss']}</td>
                    </tr>
                    <tr class="alt">
                        <td style="font-weight:bold;">IRRF</td>
                        <td style="text-align:center;">${impostos['perc_irrf']}%</td>
                        <td style="text-align:right;">R$ ${impostos['irrf']}</td>
                    </tr>
                    <tr class="alt">
                        <td style="font-weight:bold;">PCC</td>
                        <td style="text-align:center;">${impostos['perc_pcc']}%</td>
                        <td style="text-align:right;">R$ ${impostos['pcc']}</td>
                    </tr>
                    <tr class="enfase">
                        <td style="font-weight:bold;">Total Impostos</td>
                        <td style="text-align:center;"> --- </td>
                        <td style="text-align:right;">R$ ${impostos['pcc']}</td>
                    </tr>
                </tbody>
            </table>
            <hr />
            <h2><strong>** Total a Receber:</strong> R$ <span style="float:right;">${liquido}</span></h2>
            <hr />
            <strong>${partner.service_type_id.code or ''}</strong> -
            <strong>${partner.service_type_id.name or ''}</strong>
            <br />
            <strong>* A Nota fiscal deverá ser emitida com o valor Total Bruto<br />
            ** O Boleto deverá ser emitido com o valor Total a receber
            </strong>
        </div>
    </div>

    %endfor
</body>
</html>
