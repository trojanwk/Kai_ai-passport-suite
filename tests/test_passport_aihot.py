"""Exercise the actual fixed-memory ESP32 reader using synthetic public-API contracts."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class AihotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='passport-aihot-')
        folder=Path(cls.temp.name);source=folder/'test.cpp';cls.binary=folder/'test'
        source.write_text(r'''
#include "hot_board.hpp"
#include <fstream>
#include <iostream>
#include <string>
using namespace passport;
int main(int argc,char** argv){
    static_assert(sizeof(AihotJson)<3072&&sizeof(HotItem)*kHotRows<6000);
    if(argc<4)return 3;
    std::ifstream input(argv[2]);std::string body((std::istreambuf_iterator<char>(input)),{});
    const unsigned chunk=unsigned(atoi(argv[3]));HotItem rows[kHotRows]{};HotItem detail{};
    aihotCopy(detail.story,sizeof(detail.story),"event-1");
    AihotJson board(rows),story(detail);auto& parser=std::string(argv[1])=="board"?board:story;
    parser.start();for(size_t i=0;i<body.size();i+=chunk)parser.feed(body.data()+i,std::min<size_t>(chunk,body.size()-i));
    if(!parser.finish())return 2;
    if(std::string(argv[1])=="board"){
        std::cout<<parser.count()<<"\n";
        for(unsigned i=0;i<parser.count();++i)std::cout<<unsigned(rows[i].rank)<<"\t"<<rows[i].score<<"\t"<<rows[i].updated<<"\n"<<rows[i].title<<"\n"<<rows[i].source<<"\n"<<rows[i].story<<"\n";
    }else std::cout<<detail.desc<<"\n";
}
''')
        compiler=shutil.which('clang++') or shutil.which('g++')
        subprocess.run([compiler,'-std=c++20','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g','-I',str(ROOT/'firmware/passport_device/main'),str(source),'-o',str(cls.binary)],check=True)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def row(self,rank=1):
        return {'rank':rank,'id':f'item-{rank}','title':'示例模型发布 "新版本" 🚀','source':{'name':'示例信源'},'sourceCount':3,'signalCount':99,'participantCount':102,'sourceNames':['示例信源'],'latestAt':'2026-11-01T00:00:00.000Z','links':{'aihot':f'https://aihot.news/items/item-{rank}','original':'https://example.org/news','story':f'https://aihot.news/story/event-{rank}'}}

    def run_reader(self,body,mode='board',chunk=1,valid=True):
        if not isinstance(body,str):body=json.dumps(body,ensure_ascii=False)
        path=Path(self.temp.name)/'input.json';path.write_text(body)
        result=subprocess.run([str(self.binary),mode,str(path),str(chunk)],capture_output=True)
        self.assertEqual(result.returncode,0 if valid else 2,result.stderr.decode(errors='replace'))
        return result.stdout.decode('utf-8')

    def test_rank_source_counts_unicode_and_arbitrary_chunks(self):
        body={'schemaVersion':1,'count':2,'items':[self.row(1),self.row(2)]}
        for chunk in [1,2,3,7,19,185,1024]:
            with self.subTest(chunk=chunk):
                text=self.run_reader(body,chunk=chunk)
                self.assertIn('1\t3\t1793491200',text)
                self.assertIn('示例模型发布 "新版本" 🚀',text)
                self.assertIn('event-2',text)
        self.run_reader(json.dumps(body,ensure_ascii=True),chunk=1)

    def test_field_order_is_not_significant(self):
        row=dict(reversed(list(self.row().items())))
        text=self.run_reader({'items':[row],'count':1,'schemaVersion':1})
        self.assertIn('示例信源',text)

    def test_empty_board_is_valid(self):
        self.assertEqual(self.run_reader({'schemaVersion':1,'count':0,'items':[]}),'0\n')

    def test_schema_truncation_counts_and_invalid_json_are_rejected(self):
        good=json.dumps({'schemaVersion':1,'count':1,'items':[self.row()]})
        for body in [good[:-3],good+'junk','<html>blocked</html>',good.replace('"schemaVersion": 1','"schemaVersion": 2'),good.replace('"count": 1','"count": 2'),good.replace('"rank": 1','"rank": 0'),good[:-1]+',}',good.replace('"sourceCount": 3','"sourceCount": -1')]:
            with self.subTest(body=body[:60]):self.run_reader(body,valid=False)

    def test_bounds_and_nested_decoy_fields(self):
        row=self.row();row['title']='模'*500;row['unrelated']={'title':'wrong','sourceCount':999,'text':'x'*20000}
        output=self.run_reader({'schemaVersion':1,'count':1,'items':[row]})
        self.assertIn('1\t3\t',output);self.assertNotIn('wrong',output)
        self.assertLess(len(output.encode()),400)
        self.run_reader({'schemaVersion':1,'count':11,'items':[self.row(i) for i in range(1,12)]},valid=False)

    def test_story_urls_are_optional_and_restricted_to_aihot(self):
        for url in [None,'https://evil.example/story/event-1','https://aihot.news.evil/story/event-1','https://aihot.news/story/../secret','https://aihot.news/story/id?token=x']:
            row=self.row();row['links'].pop('story')
            if url is not None:row['links']['story']=url
            output=self.run_reader({'schemaVersion':1,'count':1,'items':[row]})
            self.assertTrue(output.endswith('\n\n'))

    def test_story_digest_and_fallback_are_bounded_and_identity_checked(self):
        for digest,latest,expected in [('摘要 "引号" 🚀','最新动态','摘要 "引号" 🚀'),(None,'最新动态','最新动态'),(None,'','暂无事件摘要')]:
            body={'schemaVersion':1,'story':{'publicId':'event-1','digest':digest,'latest':latest,'reports':[{'summary':'do not select another report'}]}}
            for chunk in [1,7,185]:self.assertEqual(self.run_reader(body,'story',chunk).strip(),expected)
        self.run_reader({'schemaVersion':1,'story':{'publicId':'different','digest':'wrong'}},'story',valid=False)
        text=self.run_reader({'schemaVersion':1,'story':{'publicId':'event-1','digest':'模'*1000}},'story')
        self.assertLess(len(text.encode()),242)

    def test_utc_fractional_and_offset_dates(self):
        for date in ['2026-11-01T00:00:00Z','2026-11-01T00:00:00.123456Z','2026-11-01T08:00:00+08:00']:
            row=self.row();row['latestAt']=date
            self.assertIn('1793491200',self.run_reader({'schemaVersion':1,'count':1,'items':[row]}))
        for date in ['2026-02-30T00:00:00Z','2026-11-01T24:00:00Z','2026-11-01T00:00:00','2026-11-01T00:00:00+99:00']:
            row=self.row();row['latestAt']=date
            self.run_reader({'schemaVersion':1,'count':1,'items':[row]},valid=False)

if __name__=='__main__':unittest.main()
