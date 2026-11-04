"""Execution-contract tests: next open, costs, embargo and causal gap handling."""
import unittest
import numpy as np
import pandas as pd
from replay import replay

class ReplayContract(unittest.TestCase):
 def setUp(self):
  starts=pd.date_range('2026-09-02',periods=180,freq='5min',tz='UTC')
  self.d=pd.DataFrame({'open':100.,'high':102.,'low':98.,'close':100.},index=starts+pd.Timedelta(minutes=5))
  ix=pd.date_range(starts[0],periods=900,freq='min')
  self.ex=pd.DataFrame({'open':100.+np.arange(900)*.01,'close':100.+np.arange(900)*.01},index=ix)
  self.sig=pd.Series(0,index=self.d.index);self.sig.iloc[160:163]=1
  self.lo=pd.Timestamp('2026-09-01',tz='UTC');self.hi=pd.Timestamp('2027-01-01',tz='UTC')
 def test_next_open_and_cost(self):
  t=replay(self.d,self.sig,self.ex,self.lo,self.hi,5,1.)
  self.assertEqual(len(t),1)
  r=t.iloc[0];self.assertEqual(r.entry_ts,self.d.index[160]);self.assertEqual(r.exit_ts,self.d.index[163])
  self.assertEqual(r.entry,self.ex.at[r.entry_ts,'open'])
  self.assertNotEqual(r.entry,self.d.close.iloc[160])
  self.assertAlmostEqual(r.net_px,r.exit-r.entry-1.2)
  self.assertAlmostEqual(r.stress_R,(r.exit-r.entry-1.8)/r.risk)
 def test_future_open_does_not_change_past_fill(self):
  a=replay(self.d,self.sig,self.ex,self.lo,self.hi,5,1.)
  ex=self.ex.copy();ex.loc[ex.index>self.d.index[163],'open']*=10
  b=replay(self.d,self.sig,ex,self.lo,self.hi,5,1.)
  pd.testing.assert_frame_equal(a,b)
 def test_gap_exits_at_observed_open(self):
  self.sig.iloc[160:]=1
  ent=self.d.index[160];endgap=ent+pd.Timedelta(minutes=31)
  ex=self.ex[(self.ex.index<=ent)|(self.ex.index>=endgap)]
  t=replay(self.d,self.sig,ex,self.lo,self.hi,5,1.)
  self.assertEqual(t.iloc[0].reason,'data_gap')
  self.assertEqual(t.iloc[0].exit_ts,endgap)
  self.assertEqual(t.iloc[0]['exit'],ex.at[endgap,'open'])
 def test_no_stale_entry_after_missing_open(self):
  self.sig.iloc[:]=0;self.sig.iloc[160]=1
  ex=self.ex[self.ex.index!=self.d.index[160]]
  t=replay(self.d,self.sig,ex,self.lo,self.hi,5,1.)
  self.assertTrue(t.empty)
 def test_split_does_not_carry_position(self):
  split=self.d.index[162]
  a=replay(self.d,self.sig,self.ex,self.lo,split,5,1.)
  b=replay(self.d,self.sig,self.ex,split,self.hi,5,1.)
  self.assertTrue((a.exit_ts<=split).all());self.assertTrue((b.entry_ts>=split).all())
  self.assertTrue((a.entry_ts<split).all())
if __name__=='__main__':unittest.main()
