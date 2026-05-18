"""
KIS MCP Server — stdio 방식 (이 랩탑 전용)
Claude Desktop claude_desktop_config.json 에 등록해서 사용
"""
import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta

# 머신 독립적 경로 설정
BASE_DIR = os.path.join(os.path.expanduser("~"), "open-trading-api", "examples_llm")
sys.path.insert(0, BASE_DIR)

import kis_auth as ka
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

logging.basicConfig(level=logging.WARNING)

ka.auth()
trenv = ka.getTREnv()

app = Server("kis-mcp-local")

# --- util ---

def df_to_text(df, label=""):
    if df is None or df.empty:
        return f"{label}: 데이터 없음" if label else "데이터 없음"
    return f"[{label}]\n{df.to_string(index=False)}" if label else df.to_string(index=False)

def today():
    return datetime.now().strftime("%Y%m%d")

def days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y%m%d")

# --- Tools ---

TOOL_DESCRIPTION = """한국투자증권 해외주식 API. function 파라미터로 기능을 지정하세요.

[ 시세 조회 ]
- price: 현재가. 필수: symbol, exchange
- price_detail: 현재가 상세(52주고저/PER/EPS 등). 필수: symbol, exchange
- dailyprice: 최근 30일 일봉 OHLCV. 필수: symbol, exchange

[ 차트 분석 ]
- chart_daily: 일/주/월/년봉 차트. 필수: symbol. 선택: start_date, end_date, period(D/W/M/Y). 기본 90일
- chart_minute: 분봉 차트. 필수: symbol, exchange. 선택: nmin(분갭: 1/5/10/15/30/60, 기본 5), nrec(요청건수, 기본 120)

[ 계좌/잔고 ]
- balance: 보유종목 잔고. 파라미터 불필요
- present_balance: 자산현황 상세(통화별 평가). 파라미터 불필요
- period_trans: 기간별 거래내역. 필수: start_date, end_date. 선택: symbol, exchange, trade_type(00:전체/01:매도/02:매수)
- period_profit: 기간별 실현손익. 필수: start_date, end_date. 선택: symbol, exchange

[ 시장 분석 ]
- volume_surge: 거래량 급증 종목. 필수: exchange. 선택: minx(분전: 0~9, 기본 3=5분전), vol_rang(0:전체~6:1000만주↑)
- price_fluct: 급등/급락 종목. 필수: exchange. 선택: gubn(0:급락/1:급등, 기본 1), minx(분전), vol_rang
- updown_rate: 상승/하락률 순위. 필수: exchange. 선택: nday(1~5, 기본 1), gubn(0:상승/1:하락)
- market_cap: 시가총액 순위. 필수: exchange. 선택: vol_rang

[ 종목 정보 ]
- search_info: 종목 기본정보(상장일/업종/시총 등). 필수: symbol, exchange
- news: 종목/시장 뉴스. 선택: symbol, exchange, nation_cd(US/CN/HK 등, 기본 US)

거래소 코드: NAS(나스닥), NYS(뉴욕), AMS(아멕스)
날짜 미입력시 자동으로 오늘/최근 날짜 사용
"""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "function":   {"type": "string", "description": "호출할 기능명"},
        "symbol":     {"type": "string", "description": "종목코드 (예: AAPL, NVDA, TSLA)"},
        "exchange":   {"type": "string", "description": "거래소: NAS(나스닥), NYS(뉴욕), AMS(아멕스)"},
        "start_date": {"type": "string", "description": "시작일 YYYYMMDD"},
        "end_date":   {"type": "string", "description": "종료일 YYYYMMDD"},
        "trade_type": {"type": "string", "description": "00:전체, 01:매도, 02:매수"},
        "period":     {"type": "string", "description": "차트주기 D/W/M/Y"},
        "nmin":       {"type": "string", "description": "분봉갭: 1/5/10/15/30/60"},
        "nrec":       {"type": "string", "description": "분봉 요청건수 (최대 120)"},
        "minx":       {"type": "string", "description": "N분전: 0=1분,1=2분,2=3분,3=5분,4=10분,5=15분,6=20분,7=30분,8=60분,9=120분"},
        "vol_rang":   {"type": "string", "description": "거래량조건: 0=전체,1=1백주↑,2=1천주↑,3=1만주↑"},
        "gubn":       {"type": "string", "description": "구분값 (함수마다 다름)"},
        "nday":       {"type": "string", "description": "N일자값 (updown_rate용)"},
        "nation_cd":  {"type": "string", "description": "국가코드: US/CN/HK 등"},
    },
    "required": ["function"]
}

@app.list_tools()
async def list_tools():
    return [types.Tool(name="kis_api", description=TOOL_DESCRIPTION, inputSchema=INPUT_SCHEMA)]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    fn         = arguments.get("function", "")
    symbol     = arguments.get("symbol", "")
    exchange   = arguments.get("exchange", "NAS")
    start_date = arguments.get("start_date", days_ago(90))
    end_date   = arguments.get("end_date", today())
    trade_type = arguments.get("trade_type", "00")
    period     = arguments.get("period", "D")
    nmin       = arguments.get("nmin", "5")
    nrec       = arguments.get("nrec", "120")
    minx       = arguments.get("minx", "3")
    vol_rang   = arguments.get("vol_rang", "0")
    gubn       = arguments.get("gubn", "1")
    nday       = arguments.get("nday", "1")
    nation_cd  = arguments.get("nation_cd", "US")
    cano = trenv.my_acct
    prod = trenv.my_prod

    try:
        if fn == "price":
            from overseas_stock.price.price import price
            result = df_to_text(price(auth="", excd=exchange, symb=symbol), "현재가")

        elif fn == "price_detail":
            from overseas_stock.price_detail.price_detail import price_detail
            result = df_to_text(price_detail(auth="", excd=exchange, symb=symbol), "현재가 상세")

        elif fn == "dailyprice":
            from overseas_stock.dailyprice.dailyprice import dailyprice
            _, df2 = dailyprice(auth="", excd=exchange, symb=symbol, gubn="0", bymd="", modp="1")
            result = df_to_text(df2, f"{symbol} 일봉 OHLCV")

        elif fn == "chart_daily":
            from overseas_stock.inquire_daily_chartprice.inquire_daily_chartprice import inquire_daily_chartprice
            _, df2 = inquire_daily_chartprice(
                fid_cond_mrkt_div_code="N", fid_input_iscd=symbol,
                fid_input_date_1=start_date, fid_input_date_2=end_date,
                fid_period_div_code=period,
            )
            result = df_to_text(df2, f"{symbol} {period}봉 차트")

        elif fn == "chart_minute":
            from overseas_stock.inquire_time_itemchartprice.inquire_time_itemchartprice import inquire_time_itemchartprice
            _, df2 = inquire_time_itemchartprice(
                auth="", excd=exchange, symb=symbol,
                nmin=nmin, pinc="1", next="0", nrec=nrec, fill="", keyb=""
            )
            result = df_to_text(df2, f"{symbol} {nmin}분봉")

        elif fn == "balance":
            from overseas_stock.inquire_balance.inquire_balance import inquire_balance
            df1, df2 = inquire_balance(
                cano=cano, acnt_prdt_cd=prod,
                ovrs_excg_cd="", tr_crcy_cd="USD", FK200="", NK200=""
            )
            result = df_to_text(df1, "보유종목") + "\n\n" + df_to_text(df2, "잔고요약")

        elif fn == "present_balance":
            from overseas_stock.inquire_present_balance.inquire_present_balance import inquire_present_balance
            df1, df2, df3 = inquire_present_balance(
                cano=cano, acnt_prdt_cd=prod,
                wcrc_frcr_dvsn_cd="01", natn_cd="000",
                tr_mket_cd="00", inqr_dvsn_cd="00"
            )
            result = (df_to_text(df1, "자산현황") + "\n\n" +
                      df_to_text(df2, "통화별잔고") + "\n\n" +
                      df_to_text(df3, "계좌요약"))

        elif fn == "period_trans":
            from overseas_stock.inquire_period_trans.inquire_period_trans import inquire_period_trans
            df1, df2 = inquire_period_trans(
                cano=cano, acnt_prdt_cd=prod,
                erlm_strt_dt=start_date, erlm_end_dt=end_date,
                ovrs_excg_cd=exchange, pdno=symbol,
                sll_buy_dvsn_cd=trade_type, loan_dvsn_cd="", FK100="", NK100=""
            )
            result = df_to_text(df1, "거래내역") + "\n\n" + df_to_text(df2, "합계")

        elif fn == "period_profit":
            from overseas_stock.inquire_period_profit.inquire_period_profit import inquire_period_profit
            df1, df2 = inquire_period_profit(
                cano=cano, acnt_prdt_cd=prod,
                ovrs_excg_cd=exchange, natn_cd="", crcy_cd="", pdno=symbol,
                inqr_strt_dt=start_date, inqr_end_dt=end_date, wcrc_frcr_dvsn_cd="02",
            )
            result = df_to_text(df1, "손익내역") + "\n\n" + df_to_text(df2, "손익합계")

        elif fn == "volume_surge":
            from overseas_stock.volume_surge.volume_surge import volume_surge
            df1, _ = volume_surge(excd=exchange, minx=minx, vol_rang=vol_rang)
            result = df_to_text(df1, "거래량급증")

        elif fn == "price_fluct":
            from overseas_stock.price_fluct.price_fluct import price_fluct
            df1, _ = price_fluct(excd=exchange, gubn=gubn, minx=minx, vol_rang=vol_rang)
            result = df_to_text(df1, "급등급락")

        elif fn == "updown_rate":
            from overseas_stock.updown_rate.updown_rate import updown_rate
            df1, _ = updown_rate(excd=exchange, nday=nday, gubn=gubn, vol_rang=vol_rang)
            result = df_to_text(df1, "상승하락률순위")

        elif fn == "market_cap":
            from overseas_stock.market_cap.market_cap import market_cap
            df1, _ = market_cap(excd=exchange, vol_rang=vol_rang)
            result = df_to_text(df1, "시가총액순위")

        elif fn == "search_info":
            exchange_code_map = {"NAS": "512", "NYS": "513", "AMS": "529"}
            from overseas_stock.search_info.search_info import search_info
            result = df_to_text(search_info(prdt_type_cd=exchange_code_map.get(exchange, "512"), pdno=symbol), f"{symbol} 종목정보")

        elif fn == "news":
            from overseas_stock.news_title.news_title import news_title
            result = df_to_text(news_title(
                nation_cd=nation_cd, exchange_cd=exchange, symb=symbol,
                info_gb="", class_cd="", data_dt="", data_tm="", cts=""
            ), "뉴스")

        else:
            result = f"알 수 없는 function: '{fn}'\n사용 가능 목록은 tool description 참고하세요."

    except Exception as e:
        result = f"오류 ({fn}): {str(e)}"

    return [types.TextContent(type="text", text=result)]


# --- 진입점 ---

async def main():
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
