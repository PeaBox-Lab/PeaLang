


from pealang.data import DataFrame,LazyFrame,col,coalesce

def test_inner_join():
 a=DataFrame([{'id':1,'x':'a'},{'id':2,'x':'b'}]);b=DataFrame([{'id':2,'y':9},{'id':3,'y':8}]);assert a.join(b,'id').to_dicts()==[{'id':2,'x':'b','y':9}]
def test_left_join():assert len(DataFrame([{'id':1}]).join(DataFrame([]),'id',how='left').to_dicts())==1
def test_group_agg():
 d=DataFrame([{'g':'a','v':1},{'g':'a','v':3}]).group_by('g').agg(total=('sum','v'),avg=('avg','v'));assert d.to_dicts()[0]['total']==4 and d.to_dicts()[0]['avg']==2
def test_nulls():
 d=DataFrame([{'x':None},{'x':2}]);assert d.fill_null(0).to_dicts()[0]['x']==0 and d.drop_null().row_count==1
def test_expr():
 d=DataFrame([{'x':2},{'x':4}]).with_expr('y',col('x')*2).filter_expr(col('y')>4);assert d.to_dicts()==[{'x':4,'y':8}]
def test_coalesce():assert DataFrame([{'x':None}]).with_expr('x2',coalesce(col('x'),7)).to_dicts()[0]['x2']==7
def test_pivot_unpivot():
 d=DataFrame([{'id':1,'k':'a','v':2},{'id':1,'k':'b','v':3}]);p=d.pivot('id','k','v');assert p.to_dicts()[0]['a']==2 and p.unpivot('id',['a','b']).row_count==2
def test_window_row_number():
 d=DataFrame([{'g':'a','v':2},{'g':'a','v':1}]).window('g','v');assert [r['row_number'] for r in d.to_dicts()]==[1,2]
def test_lazy_group():
 l=LazyFrame(lambda:DataFrame([{'g':'a','v':1},{'g':'a','v':2}])).group_by('g').agg(total=('sum','v'));assert l.collect().to_dicts()[0]['total']==3 and 'group_by/agg' in l.explain()



