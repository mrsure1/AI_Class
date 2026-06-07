/**
 * AI 기초교육 - 참가자 사전 설문 → 구글 시트 연동
 *
 * 시트 ID: 1giowEACfpBA_3fBqyQnsXg4Tojtfw53HGDNlWGVWvrI
 * 동작: 기존 접수 행(이름·연락처 등)은 유지하고, 설문 열만 해당 행에 기록
 */

var SPREADSHEET_ID = '1giowEACfpBA_3fBqyQnsXg4Tojtfw53HGDNlWGVWvrI';

var SURVEY_HEADERS = [
  '설문작성일시',
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
  return ss.getSheets()[0];
}

function ensureSurveyHeaders_(sheet) {
  var lastCol = sheet.getLastColumn();
  if (lastCol < 1) return;

  var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  var headerSet = {};
  headers.forEach(function (h) {
    headerSet[String(h).trim()] = true;
  });

  var missing = SURVEY_HEADERS.filter(function (h) {
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

    return jsonResponse_({ ok: true, message: '설문이 저장되었습니다.', row: row });
  } catch (err) {
    return jsonResponse_({ ok: false, message: err.message || String(err) });
  }
}
