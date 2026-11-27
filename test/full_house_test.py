"""A whole house with one blank, and its native full-unit forced-fill story."""
from pathlib import Path
import copy,importlib.util,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('full_house_rules',ROOT/'tools/validate_lessons.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

def example(kind='row'):
    grid=[(r*3+r//3+c)%9+1 for r in range(9) for c in range(9)]
    cell=40;digit=grid[cell];grid[cell]=0
    index={'row':cell//9,'column':cell%9,'box':cell//27*3+cell%9//3}[kind]
    e={'grid':''.join(map(str,grid)),'unit':kind,'unitIndex':index,'cell':cell,'digit':digit}
    values,units,_=p.position(e);unit=units[{'row':0,'column':9,'box':18}[kind]+index]
    e['unitGivens']=[[i,values[i]] for i in sorted(unit) if values[i]]
    return e

class FullHouse(unittest.TestCase):
    def test_row_column_box_and_whole_grid_last_digit_follow_the_same_rule(self):
        for kind in ['row','column','box']:
            e=example(kind);p.PROOFS['full-house'](e);p.unique_solution(e['grid'])

    def test_wrong_unit_choice_incomplete_or_noninteger_witnesses_are_rejected(self):
        e=example()
        for key,value in [('unit','diagonal'),('unitIndex',True),('cell',True),('digit',0),
                          ('unitGivens',e['unitGivens'][:-1])]:
            with self.subTest(key=key):
                changed={**e,key:value}
                with self.assertRaises(ValueError):p.PROOFS['full-house'](changed)
        for value in [True,1.0]:
            changed=copy.deepcopy(e);changed['unitGivens'][0][1]=value
            with self.assertRaisesRegex(ValueError,'integer'):p.PROOFS['full-house'](changed)
        changed=copy.deepcopy(e);j=e['unitGivens'][0][0];g=list(changed['grid']);g[j]='0';changed['grid']=''.join(g)
        with self.assertRaisesRegex(ValueError,'exactly one blank'):p.PROOFS['full-house'](changed)
        changed={**e,'digit':e['digit']%9+1}
        with self.assertRaises(ValueError):p.PROOFS['full-house'](changed)

    def test_full_house_native_reveal_is_a_whole_unit_not_a_naked_single_cell(self):
        e=example('column');i,d=e['cell'],e['digit'];q=[i//9,i%9,d]
        story={'style':'chill','frames':[{'do':'tap','count':2,'at':{'part':'cell','cell':q[:2]}}],
               'expected':{'initialStatus':'definite','initialSingle':q,'boards':1,'slotFills':[[0,*q]],
                           'fills':[q],'validSlots':[0],'overlays':[],'revealFrameCount':1,'revealLabelCount':1},
               'presentation':{'choiceReveal':{'frames':[[0,4,9,1]],'labels':[q]}}}
        check=lambda data:p._full_house.validate_story(data,e,p.forced_single_animation,p.require)
        check(story)
        for category,key,value in [('reveal','frames',[[4,4,1,1]]),('checks','revealFrameCount',0),
                                   ('checks','revealLabelCount',0),('checks','initialStatus','dilemma')]:
            changed=copy.deepcopy(story);target=changed['expected'] if category=='checks' else changed['presentation']['choiceReveal'];target[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):check(changed)
        with self.assertRaises(ValueError):check({**story,'style':'dilemma'})

if __name__=='__main__':unittest.main()
