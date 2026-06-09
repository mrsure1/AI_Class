/**
 * AI 기초교육 - 참가자 사전 설문 → 구글 시트 연동
 *
 * 시트 ID: 1giowEACfpBA_3fBqyQnsXg4Tojtfw53HGDNlWGVWvrI
 * 동작: 기존 접수 행(이름·연락처 등)은 유지하고, 설문 열만 해당 행에 기록
 */

var SPREADSHEET_ID = '1giowEACfpBA_3fBqyQnsXg4Tojtfw53HGDNlWGVWvrI';

var SURVEY_HEADERS = [
  '컴퓨터사용능력',
  'AI경험',
  'AI하고싶은것',
  'AI기타',
  '보유기기',
  '설문완료'
];

function normalizePhone(phone) {
  return String(phone || '').replace(/[^0-9]/g, '');
}

function getSheet_() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheet = ss.getSheetByName("설문작성");
  if (!sheet) {
    sheet = ss.insertSheet("설문작성");
  }
  return sheet;
}

function ensureSurveyHeaders_(sheet) {
  var lastCol = sheet.getLastColumn();
  var allHeaders = ['설문작성일시', '이름', '연락처'].concat(SURVEY_HEADERS);
  
  if (lastCol < 1) {
    sheet.getRange(1, 1, 1, allHeaders.length).setValues([allHeaders]);
    sheet.getRange(1, 1, 1, allHeaders.length).setFontWeight('bold');
    return;
  }

  var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  var headerSet = {};
  headers.forEach(function (h) {
    headerSet[String(h).trim()] = true;
  });

  var missing = allHeaders.filter(function (h) {
    return !headerSet[h];
  });

  if (missing.length === 0) return;

  var startCol = lastCol + 1;
  sheet.getRange(1, startCol, 1, missing.length).setValues([missing]);
  sheet.getRange(1, startCol, 1, missing.length).setFontWeight('bold');
}

function getHeaderIndexMap_(sheet) {
  var lastCol = sheet.getLastColumn();
  var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  var map = {};
  headers.forEach(function (h, i) {
    map[String(h).trim()] = i + 1;
  });
  return map;
}

function findRowByContact_(sheet, name, phone) {
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) return -1;

  var headers = data[0];
  var phoneCol = -1;
  var nameCol = -1;

  headers.forEach(function (h, i) {
    var key = String(h).trim();
    if (key === '연락처') phoneCol = i;
    if (key === '이름') nameCol = i;
  });

  if (phoneCol === -1) {
    throw new Error('시트에 "연락처" 열이 없습니다.');
  }

  var normalizedPhone = normalizePhone(phone);
  if (!normalizedPhone) return -1;

  var trimmedName = String(name || '').trim();
  var phoneMatchRow = -1;

  for (var r = 1; r < data.length; r++) {
    var rowPhone = normalizePhone(data[r][phoneCol]);
    if (rowPhone !== normalizedPhone) continue;

    phoneMatchRow = r + 1;

    if (!trimmedName || nameCol === -1) {
      return phoneMatchRow;
    }

    var rowName = String(data[r][nameCol] || '').trim();
    if (rowName === trimmedName) {
      return r + 1;
    }
  }

  return phoneMatchRow;
}

function jsonResponse_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet() {
  return jsonResponse_({ ok: true, message: 'AI survey endpoint ready' });
}

function doPost(e) {
  try {
    var raw = (e && e.postData && e.postData.contents) ? e.postData.contents : '{}';
    var data = JSON.parse(raw);

    var name = String(data.name || '').trim();
    var phone = String(data.phone || '').trim();

    if (!name) {
      return jsonResponse_({ ok: false, message: '이름을 입력해 주세요.' });
    }
    if (!normalizePhone(phone)) {
      return jsonResponse_({ ok: false, message: '연락처를 입력해 주세요.' });
    }

    var sheet = getSheet_();
    ensureSurveyHeaders_(sheet);

    var colMap = getHeaderIndexMap_(sheet);
    var row = findRowByContact_(sheet, name, phone);
    if (row === -1) {
      // 일치하는 행이 없으면 새로운 행을 추가합니다.
      row = sheet.getLastRow() + 1;
      if (colMap['이름']) {
        sheet.getRange(row, colMap['이름']).setValue(name);
      }
      if (colMap['연락처']) {
        sheet.getRange(row, colMap['연락처']).setValue(phone);
      }
    }
    var now = Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy-MM-dd HH:mm');

    sheet.getRange(row, colMap['설문작성일시']).setValue(now);
    sheet.getRange(row, colMap['컴퓨터사용능력']).setValue(String(data.computer || ''));
    sheet.getRange(row, colMap['AI경험']).setValue(String(data.aiExperience || ''));
    sheet.getRange(row, colMap['AI하고싶은것']).setValue(String(data.wants || ''));
    sheet.getRange(row, colMap['AI기타']).setValue(String(data.otherWant || ''));
    sheet.getRange(row, colMap['보유기기']).setValue(String(data.devices || ''));
    sheet.getRange(row, colMap['설문완료']).setValue('Y');

    // ==========================================
    // [알림 발송] 설문 접수 실시간 메시지 발송
    // ==========================================
    var alertText = "🔔 <b>새로운 설문조사 접수 완료!</b>\n\n" +
                    "👤 이름: " + name + "\n" +
                    "📞 연락처: " + phone + "\n" +
                    "💻 컴퓨터 능력: " + String(data.computer || '') + "\n" +
                    "🤖 AI 경험: " + String(data.aiExperience || '') + "\n" +
                    "📝 하고 싶은 것: " + String(data.wants || '');
    
    // [알림 발송] Apps Script 스크립트 속성에 TELEGRAM_TOKEN, TELEGRAM_CHAT_ID 등록 시 자동 발송
    sendTelegramAlert_(alertText);
    // sendDiscordAlert_(alertText.replace(/<[^>]*>/g, '')); // Discord용 HTML 태그 제거

    return jsonResponse_({ ok: true, message: '설문이 저장되었습니다.', row: row });
  } catch (err) {
    return jsonResponse_({ ok: false, message: err.message || String(err) });
  }
}

/**
 * 텔레그램 알림 발송 도우미 함수 (100% 무료, 추천)
 */
function sendTelegramAlert_(text) {
  var token = PropertiesService.getScriptProperties().getProperty('TELEGRAM_TOKEN');
  var chatId = PropertiesService.getScriptProperties().getProperty('TELEGRAM_CHAT_ID');
  if (!token || !chatId) {
    return { skipped: true, reason: 'TELEGRAM_TOKEN 또는 TELEGRAM_CHAT_ID 스크립트 속성이 없음', hasToken: !!token, hasChatId: !!chatId };
  }

  var url = 'https://api.telegram.org/bot' + token + '/sendMessage';
  var payload = {
    'chat_id': chatId,
    'text': text,
    'parse_mode': 'HTML'
  };
  var options = {
    'method': 'post',
    'contentType': 'application/json',
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true
  };
  try {
    var resp = UrlFetchApp.fetch(url, options);
    return { skipped: false, status: resp.getResponseCode(), body: resp.getContentText() };
  } catch (err) {
    return { skipped: false, error: String(err) };
  }
}

/**
 * 디스코드 웹훅 알림 발송 도우미 함수 (100% 무료, 추천)
 */
function sendDiscordAlert_(text) {
  var webhookUrl = '여기에_디스코드_웹훅_URL_입력';
  if (webhookUrl === '여기에_디스코드_웹훅_URL_입력') return;

  var payload = {
    'content': text
  };
  var options = {
    'method': 'post',
    'contentType': 'application/json',
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true
  };
  UrlFetchApp.fetch(webhookUrl, options);
}
