
-- Ajustar STATE da fatura

select state 
from account_invoice
where state in ('sefaz_export','sefaz_exception')

begin transaction

update account_invoice
set state = 'open'
where state in ('sefaz_export','sefaz_exception')

rollback

commit

-- Atualizar o wkf_workitem

select 		ww.id,
		ww.act_id,
		wa.id,
		wa.name,
		wk.id,
		wk.name
from 		wkf_workitem as ww
inner join 	wkf_activity as wa on (ww.act_id=wa.id)
inner join	wkf as wk on (wa.wkf_id=wk.id)
where		wk.name = 'account.invoice.basic'


begin transaction

update 	wkf_workitem
set 	act_id =  (select wkf_activity.id
		   from   wkf_activity 
		   where  wkf_activity.wkf_id in (select id from wkf where wkf.name='account.invoice.basic')
		   and 	  wkf_activity.name = 'open')
where 	act_id in (select wkf_activity.id
		   from   wkf_activity 
		   where  wkf_activity.wkf_id in (select id from wkf where wkf.name='account.invoice.basic')
		   and 	  wkf_activity.name in ('sefaz_export', 'sefaz_exception', 'sefaz_transmit', 'router', 'proforma2'))

rollback

commit

-- Atualizar o wkf_triggers

BEGIN TRANSACTION

    INSERT INTO wkf_triggers (instance_id, workitem_id, model, res_id)
        (SELECT	wi.id AS wi_id,
		ww.id AS ww_id,
		'account.move.line'::text AS model,
		aml.id AS aml_id
           FROM	account_invoice AS ai
     INNER JOIN account_move_line AS aml ON (aml.move_id = ai.move_id)
     INNER JOIN wkf_instance AS wi ON (wi.res_id = ai.id)
     INNER JOIN wkf_workitem AS ww ON (ww.inst_id = wi.id)
          WHERE ai.date_due > '2015-06-01' 
            AND	ai.state = 'open' 
            AND	ai.residual > 0.0 
            AND ai.residual = ai.amount_total
            AND aml.debit > 0.0
            AND wi.res_type = 'account.invoice' 
            AND NOT EXISTS (SELECT 1
			    FROM wkf_triggers AS wt
			   WHERE wt.instance_id = wi.id
			     AND wt.workitem_id = ww.id
			     AND wt.model = 'account.move.line'::text
			     AND wt.res_id = aml.id))

ROLLBACK

COMMIT


