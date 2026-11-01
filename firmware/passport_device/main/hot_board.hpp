#pragma once
#include "../../passport_suite/main/apps.hpp"
#include <algorithm>
#include <cctype>
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace passport {
// Ten bounded rows use approximately the same RAM as the previous twenty Baidu rows.
struct HotItem {
    char title[144]{},desc[240]{},source[64]{},story[65]{};
    uint32_t score{},updated{};uint8_t tag{},rank{};bool detail{};
};
inline void aihotCopy(char* out,size_t capacity,const char* in){
    size_t n=std::min(strlen(in),capacity-1);
    while(n&&(static_cast<unsigned char>(in[n])&0xc0)==0x80)--n;
    memcpy(out,in,n);out[n]=0;
}
inline uint32_t aihotEpoch(const char* text){
    unsigned y,m,d,h,minute,s;int n=0;
    if(sscanf(text,"%4u-%2u-%2uT%2u:%2u:%2u%n",&y,&m,&d,&h,&minute,&s,&n)!=6||n!=19||y<1970||y>2106||m<1||m>12||h>23||minute>59||s>59)return 0;
    constexpr unsigned days[]{31,28,31,30,31,30,31,31,30,31,30,31};
    if(!d||d>days[m-1]+unsigned(m==2&&y%4==0&&(y%100!=0||y%400==0)))return 0;
    const char* zone=text+n;if(*zone=='.'){++zone;if(!isdigit(static_cast<unsigned char>(*zone)))return 0;while(isdigit(static_cast<unsigned char>(*zone)))++zone;}
    int offset=0;
    if(*zone=='Z'&&!zone[1]){}
    else if((*zone=='+'||*zone=='-')&&strlen(zone)==6&&zone[3]==':'&&isdigit(zone[1])&&isdigit(zone[2])&&isdigit(zone[4])&&isdigit(zone[5])){
        unsigned hours=(zone[1]-'0')*10+zone[2]-'0',minutes=(zone[4]-'0')*10+zone[5]-'0';if(hours>23||minutes>59)return 0;
        offset=int(hours*3600+minutes*60)*(*zone=='+'?1:-1);
    }else return 0;
    const int year=int(y)-(m<=2),era=year/400;const unsigned yo=year-era*400,mp=m>2?m-3:m+9;
    const int64_t date=int64_t(era)*146097+yo*365+yo/4-yo/100+(153*mp+2)/5+d-1-719468;
    const int64_t epoch=date*86400+h*3600+minute*60+s-offset;
    return epoch>0&&epoch<=UINT32_MAX?uint32_t(epoch):0;
}
inline bool aihotStoryId(char* out,size_t capacity,const char* url){
    constexpr char prefix[]="https://aihot.news/story/";
    if(strncmp(url,prefix,sizeof(prefix)-1))return false;
    const char* id=url+sizeof(prefix)-1;const size_t n=strlen(id);
    if(!n||n>=capacity)return false;
    for(const char* p=id;*p;++p)if(!isalnum(static_cast<unsigned char>(*p))&&*p!='-'&&*p!='_')return false;
    memcpy(out,id,n+1);return true;
}

// Fixed-memory JSON SAX reader: no body or DOM is retained. Field order and wire chunks are arbitrary.
class AihotJson {
public:
    explicit AihotJson(HotItem* rows):rows_(rows){}
    explicit AihotJson(HotItem& detail):detail_(&detail){}
    void start(){depth_=used_=hex_=code_=high_=count_=declared_=schema_=seen_=0;bad_=done_=string_=escape_=raw_=key_=truncated_=haveCount_=haveItems_=storySeen_=false;next_={};digest_[0]=latest_[0]=storyId_[0]=0;}
    void feed(const char* bytes,size_t size){for(size_t i=0;i<size&&!bad_;++i)put(bytes[i]);}
    bool finish(){
        if(raw_){raw_=false;scalar(false);}
        if(bad_||!done_||depth_||string_||hex_||high_||schema_!=1)return false;
        if(rows_)return haveItems_&&haveCount_&&declared_==count_;
        if(!storySeen_||!detail_||strcmp(detail_->story,storyId_))return false;
        aihotCopy(detail_->desc,sizeof(detail_->desc),*digest_?digest_:*latest_?latest_:"暂无事件摘要");detail_->detail=true;return true;
    }
    unsigned count()const{return count_;}
private:
    struct Frame{char kind;uint8_t state{};unsigned index{};char key[64]{};} frames_[12]{};
    HotItem* rows_{};HotItem* detail_{};HotItem next_{};
    unsigned depth_{},used_{},hex_{},code_{},high_{},count_{},declared_{},schema_{},seen_{};
    bool bad_{},done_{},string_{},escape_{},raw_{},key_{},truncated_{},haveCount_{},haveItems_{},storySeen_{};
    char token_[512]{},digest_[240]{},latest_[240]{},storyId_[65]{};
    void add(char c){if(used_+1<sizeof(token_))token_[used_++]=c;else truncated_=true;}
    void utf8(unsigned code){if(code<0x80){if(!code){bad_=true;return;}add(char(code));}else if(code<0x800){add(char(0xc0|(code>>6)));add(char(0x80|(code&63)));}else if(code<0x10000){add(char(0xe0|(code>>12)));add(char(0x80|((code>>6)&63)));add(char(0x80|(code&63)));}else{add(char(0xf0|(code>>18)));add(char(0x80|((code>>12)&63)));add(char(0x80|((code>>6)&63)));add(char(0x80|(code&63)));}}
    void complete(){if(!depth_){done_=true;return;}auto& f=frames_[depth_-1];if(f.kind=='{')f.state=3;else{f.state=1;++f.index;}}
    bool expecting()const{if(!depth_)return !done_;const auto& f=frames_[depth_-1];return f.kind=='{'?f.state==2:f.state==0||f.state==2;}
    bool boardRow()const{return rows_&&depth_>=3&&!strcmp(frames_[0].key,"items")&&frames_[1].kind=='['&&frames_[2].kind=='{';}
    static bool integer(const char* value,unsigned& out){if(!*value)return false;for(const char* p=value;*p;++p)if(!isdigit(static_cast<unsigned char>(*p)))return false;char* end;errno=0;const unsigned long n=strtoul(value,&end,10);if(errno||*end||n>UINT32_MAX)return false;out=unsigned(n);return true;}
    void field(bool quoted){
        if(!depth_)return;
        const auto& f=frames_[depth_-1];
        if(depth_==1&&!strcmp(f.key,"schemaVersion")){if(quoted||!integer(token_,schema_))bad_=true;}
        if(rows_&&depth_==1&&!strcmp(f.key,"count")){haveCount_=true;if(quoted||!integer(token_,declared_)||declared_>kHotRows)bad_=true;}
        if(boardRow()){
            if(depth_==3){
                if(!strcmp(f.key,"title")){if(!quoted||!*token_)bad_=true;else{aihotCopy(next_.title,sizeof(next_.title),token_);seen_|=1;}}
                if(!strcmp(f.key,"rank")){unsigned rank;if(quoted||!integer(token_,rank)||rank!=count_+1)bad_=true;else{next_.rank=uint8_t(rank);seen_|=2;}}
                if(!strcmp(f.key,"sourceCount")){unsigned sources;if(quoted||!integer(token_,sources))bad_=true;else{next_.score=uint32_t(sources);seen_|=4;}}
                if(!strcmp(f.key,"latestAt")){next_.updated=quoted?aihotEpoch(token_):0;if(!next_.updated)bad_=true;else seen_|=8;}
            }
            if(depth_==4&&!strcmp(frames_[2].key,"source")&&!strcmp(f.key,"name")&&quoted){aihotCopy(next_.source,sizeof(next_.source),token_);seen_|=16;}
            if(depth_==4&&!strcmp(frames_[2].key,"links")&&!strcmp(f.key,"story")&&quoted)aihotStoryId(next_.story,sizeof(next_.story),token_);
        }
        if(detail_&&depth_==2&&!strcmp(frames_[0].key,"story")){
            storySeen_=true;
            if(!strcmp(f.key,"publicId")&&quoted&&!truncated_)aihotCopy(storyId_,sizeof(storyId_),token_);
            if(!strcmp(f.key,"digest")&&quoted)aihotCopy(digest_,sizeof(digest_),token_);
            if(!strcmp(f.key,"latest")&&quoted)aihotCopy(latest_,sizeof(latest_),token_);
        }
    }
    void scalar(bool quoted){
        token_[used_]=0;
        // Drop an incomplete UTF-8 character from a truncated retained prefix.
        if(truncated_){size_t n=used_,at=n;while(at&&(static_cast<unsigned char>(token_[at-1])&0xc0)==0x80)--at;if(at){const unsigned char lead=token_[at-1];const unsigned want=lead<0x80?1:lead>=0xf0?4:lead>=0xe0?3:lead>=0xc0?2:1;if(n-(at-1)<want)token_[at-1]=0;}}
        if(!quoted){
            if(truncated_){bad_=true;return;}
            const char* p=token_;if(*p=='-')++p;bool numeric=false;
            if(*p=='0'){++p;numeric=true;}else if(*p>='1'&&*p<='9'){numeric=true;while(isdigit(static_cast<unsigned char>(*p)))++p;}
            if(numeric&&*p=='.'){++p;if(!isdigit(static_cast<unsigned char>(*p)))numeric=false;while(isdigit(static_cast<unsigned char>(*p)))++p;}
            if(numeric&&(*p=='e'||*p=='E')){++p;if(*p=='+'||*p=='-')++p;if(!isdigit(static_cast<unsigned char>(*p)))numeric=false;while(isdigit(static_cast<unsigned char>(*p)))++p;}
            if((!numeric||*p)&&strcmp(token_,"null")&&strcmp(token_,"true")&&strcmp(token_,"false")){bad_=true;return;}
        }
        field(quoted);complete();used_=0;truncated_=false;
    }
    void put(char c){
        if(hex_){const unsigned h=c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:c>='A'&&c<='F'?c-'A'+10:99;if(h==99){bad_=true;return;}code_=code_*16+h;
            if(!--hex_){if(code_>=0xd800&&code_<=0xdbff){if(high_)bad_=true;else high_=code_;}else if(code_>=0xdc00&&code_<=0xdfff){if(!high_)bad_=true;else{utf8(0x10000+((high_-0xd800)<<10)+code_-0xdc00);high_=0;}}else if(high_)bad_=true;else utf8(code_);}return;}
        if(string_){
            if(escape_){escape_=false;if(c=='u'){hex_=4;code_=0;}else if(high_)bad_=true;else if(c=='"'||c=='\\'||c=='/')add(c);else if(strchr("bfnrt",c))add(' ');else bad_=true;return;}
            if(c=='\\'){escape_=true;return;}if(high_){bad_=true;return;}
            if(c=='"'){string_=false;token_[used_]=0;if(key_){auto& f=frames_[depth_-1];if(truncated_||used_>=sizeof(f.key)){bad_=true;return;}strcpy(f.key,token_);f.state=1;used_=0;truncated_=false;}else scalar(true);}
            else if(static_cast<unsigned char>(c)<32)bad_=true;else add(c);
            return;
        }
        if(raw_){if(c!=','&&c!='}'&&c!=']'&&!isspace(static_cast<unsigned char>(c))){add(c);return;}raw_=false;scalar(false);if(bad_)return;}
        if(isspace(static_cast<unsigned char>(c)))return;
        if(c=='}'||c==']'){
            if(!depth_){bad_=true;return;}const auto& f=frames_[depth_-1];if((c=='}'&&(f.kind!='{'||(f.state!=0&&f.state!=3)))||(c==']'&&(f.kind!='['||(f.state!=0&&f.state!=1)))){bad_=true;return;}
            if(boardRow()&&depth_==3){if(seen_!=31||count_>=kHotRows){bad_=true;return;}rows_[count_++]=next_;next_={};seen_=0;}
            --depth_;complete();return;
        }
        if(depth_){auto& f=frames_[depth_-1];if(c==':'&&f.kind=='{'&&f.state==1){f.state=2;return;}if(c==','&&((f.kind=='{'&&f.state==3)||(f.kind=='['&&f.state==1))){f.state=f.kind=='{'?4:2;return;}if(f.kind=='{'&&(f.state==0||f.state==4)&&c=='"'){string_=key_=true;used_=0;truncated_=false;return;}}
        if(!expecting()){bad_=true;return;}
        if(c=='{'||c=='['){if(depth_==12){bad_=true;return;}if(rows_&&depth_==1&&!strcmp(frames_[0].key,"items")){if(c!='['){bad_=true;return;}haveItems_=true;}frames_[depth_++]={c};return;}
        used_=0;truncated_=false;key_=false;if(c=='"')string_=true;else{raw_=true;add(c);}
    }
};
}
