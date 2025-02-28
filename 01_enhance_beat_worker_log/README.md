# <span id="title">Improving Celery Task Log Traceability</span>

<span id="description">
這篇紀錄旨在探討如何提升 Celery 記錄的可追蹤性和閱讀性，讓管理和除錯過程更為高效。
</span>

## 1. Challenges in Log Tracking

在使用 Celery 處理大量任務時，分析其原始 log 往往會面臨以下問題：

- **任務追蹤困難**：大量 log 中難以快速定位特定任務的相關訊息。
- **缺乏清晰的上下文連結**：log 條目之間的依賴關係不明顯，尤其是跨任務的觸發與父子關係。
- **記錄冗長**：重複且缺乏重點的訊息，增加了閱讀與分析的負擔。

e.g.:

```
[2023-12-30 10:46:38,196: INFO/MainProcess] Scheduler: Sending due task test-nested-job (app.task.first_task
[2023-12-30 10:46:38,219: INFO/MainProcess] Task app.task.first_task[dd1834ad-4af0-4ae3-bac4-41d90b8732ae] received
[2023-12-30 10:46:38,220: INFO/MainProcess] Debug task 1
[2023-12-30 10:46:38,267: INFO/MainProcess] Task app.task.second_debug_task[498bfe63-e072-44b9-be9f-5078bf78cca2] received
[2023-12-30 10:46:38,274: INFO/MainProcess] Task app.task.first_task[dd1834ad-4af0-4ae3-bac4-41d90b8732ae] succeeded in 0.05412780500000025s: None
[2023-12-30 10:46:38,276: INFO/MainProcess] Debug task 2
[2023-12-30 10:46:38,352: INFO/MainProcess] Task app.task.second_debug_task[a9edbc93-aa0c-45c4-8829-d7ef24fc50c1] received
[2023-12-30 10:46:38,367: INFO/MainProcess] Task app.task.second_debug_task[498bfe63-e072-44b9-be9f-5078bf78cca2] succeeded in 0.09155484199999986s: None
[2023-12-30 10:46:38,369: INFO/MainProcess] Debug task 2
[2023-12-30 10:46:38,442: INFO/MainProcess] Task app.task.third_debug_task[c59a94fb-5a74-40a8-93c0-9c36242f293f] received
[2023-12-30 10:46:38,461: INFO/MainProcess] Task app.task.second_debug_task[a9edbc93-aa0c-45c4-8829-d7ef24fc50c1] succeeded in 0.0920364410000003s: None
[2023-12-30 10:46:38,463: INFO/MainProcess] Debug task 3
[2023-12-30 10:46:38,527: INFO/MainProcess] Task app.task.fourth_debug_task[ac8dd0f7-edfc-458a-a089-6d4fc102c8bc] received
[2023-12-30 10:46:38,536: INFO/MainProcess] Task app.task.third_debug_task[c59a94fb-5a74-40a8-93c0-9c36242f293f] succeeded in 0.07286700600000007s: None
[2023-12-30 10:46:38,537: INFO/MainProcess] Debug task 4
[2023-12-30 10:46:38,576: INFO/MainProcess] Task app.task.third_debug_task[b174ad0c-7005-45af-a4a5-25362a9bb6ed] received
[2023-12-30 10:46:38,582: INFO/MainProcess] Task app.task.fourth_debug_task[ac8dd0f7-edfc-458a-a089-6d4fc102c8bc] succeeded in 0.04526384800000027s: None
[2023-12-30 10:46:38,583: INFO/MainProcess] Debug task 3
[2023-12-30 10:46:38,627: INFO/MainProcess] Task app.task.fourth_debug_task[ebfca86d-f5a0-4160-85d2-bbf3973b5e47] received
[2023-12-30 10:46:38,635: INFO/MainProcess] Task app.task.third_debug_task[b174ad0c-7005-45af-a4a5-25362a9bb6ed] succeeded in 0.052080793000000014s: None
[2023-12-30 10:46:38,636: INFO/MainProcess] Debug task 4
[2023-12-30 10:46:38,678: INFO/MainProcess] Task app.task.fourth_debug_task[b10dcf33-8493-4471-81c9-aec86a9a53c5] received
[2023-12-30 10:46:38,683: INFO/MainProcess] Task app.task.fourth_debug_task[ebfca86d-f5a0-4160-85d2-bbf3973b5e47] succeeded in 0.047611055000000846s: None
[2023-12-30 10:46:38,684: INFO/MainProcess] Debug task 4
[2023-12-30 10:46:38,725: INFO/MainProcess] Task app.task.fourth_debug_task[13d421f1-120e-4e41-804c-9133a9ef2a66] received
[2023-12-30 10:46:38,727: INFO/MainProcess] Task app.task.fourth_debug_task[b10dcf33-8493-4471-81c9-aec86a9a53c5] succeeded in 0.042970032999999574s: None
[2023-12-30 10:46:38,728: INFO/MainProcess] Debug task 4
[2023-12-30 10:46:38,769: INFO/MainProcess] Task app.task.fourth_debug_task[13d421f1-120e-4e41-804c-9133a9ef2a66] succeeded in 0.04080406000000103s: None
```

<br>

## 2. Initial Optimization: Introducing `asgi-correlation-id`

為了解決上述問題，採用了 [asgi-correlation-id](https://github.com/snok/asgi-correlation-id) 套件，為每個任務生成獨特的識別碼 (correlation ID)，並結合 Celery 任務的上下文資訊進行 log 優化。

### 解決方案概述

以下是優化方案的關鍵步驟：

1. **整合 correlation ID 與 Celery 的 task_id**：自動將上下文 ID 添加到每條 log 條目中。
2. **格式化輸出**：使用更清晰的 log 格式，顯示任務關聯的父子 ID。
3. **過濾冗餘訊息**：忽略不必要的系統訊息，僅保留重要內容。

#### 具體實現

在 Celery 初始化時載入相關功能：

```python
from asgi_correlation_id.extensions.celery import load_correlation_ids

load_correlation_ids()
load_celery_current_and_parent_ids(use_internal_celery_task_id=True)
```

新增自定義 log 過濾器與格式化器：

```python
@after_setup_logger.connect(weak=False)
def on_after_setup_logger(logger, *args, **kwargs):
    correlation_id_filter = asgi_correlation_id.CorrelationIdFilter(default_value=' ' * 8)
    celery_tracing_filter = asgi_correlation_id.CeleryTracingIdsFilter(default_value=' ' * 8)
    formatter = colorlog.ColoredFormatter(
        fmt='%(levelname)-8s [%(correlation_id)s] [%(celery_parent_id)s] [%(celery_current_id)s] %(name)s | %(message)s'
    )
    handler = colorlog.StreamHandler()
    handler.addFilter(correlation_id_filter)
    handler.addFilter(celery_tracing_filter)
    handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(handler)
```

<br>

## 3. Optimized Log

引入 correlation ID 和任務層級上下文後，log 更加清晰，能快速追蹤任務的執行狀態與依賴關係：

```
       process-id
           |    correlation-id          current-id
           |          |      parent-id      |
           |          |          |          |
INFO     | 1  |          |          |          | celery.beat            | Scheduler: Sending due task test-nested-job (app.task.first_task)
INFO     | 1  |          |          |          | celery.worker.strategy | Task app.task.first_task[a3e5d1af-5636-49e6-aff9-86a3e3a766c5] received
INFO     | 9  | 9a276155 | None     | a3e5d1af | app.task               | Debug task 1
INFO     | 1  |          |          |          | celery.worker.strategy | Task app.task.second_debug_task[c7606e5f-c6ce-45c0-8366-c86c1d56e155] received
INFO     | 9  | 9a276155 | None     | a3e5d1af | celery.app.trace       | Task app.task.first_task[a3e5d1af-5636-49e6-aff9-86a3e3a766c5] succeeded in 0.003938464000384556s: None
INFO     | 8  | 9a276155 | a3e5d1af | c7606e5f | app.task               | Debug task 2
INFO     | 1  |          |          |          | celery.worker.strategy | Task app.task.second_debug_task[6714d40b-b33d-4996-8913-8dbe823d805d] received
INFO     | 9  | 9a276155 | a3e5d1af | 6714d40b | app.task               | Debug task 2
INFO     | 8  | 9a276155 | a3e5d1af | c7606e5f | celery.app.trace       | Task app.task.second_debug_task[c7606e5f-c6ce-45c0-8366-c86c1d56e155] succeeded in 0.0042529099991952535s: None
INFO     | 1  |          |          |          | celery.worker.strategy | Task app.task.third_debug_task[0a17ee29-20c1-43bc-9a0a-da19d5bd90a7] received
INFO     | 1  |          |          |          | celery.worker.strategy | Task app.task.fourth_debug_task[697eb405-3977-4fee-8287-09767d48bf24] received
INFO     | 9  | 9a276155 | a3e5d1af | 6714d40b | celery.app.trace       | Task app.task.second_debug_task[6714d40b-b33d-4996-8913-8dbe823d805d] succeeded in 0.004168741999819758s: None
INFO     | 1  |          |          |          | celery.worker.strategy | Task app.task.third_debug_task[5f91f483-e28d-4f5b-8eff-304c3e42eb06] received
INFO     | 9  | 9a276155 | c7606e5f | 0a17ee29 | app.task               | Debug task 3
INFO     | 8  | 9a276155 | c7606e5f | 697eb405 | app.task               | Debug task 4
INFO     | 8  | 9a276155 | c7606e5f | 697eb405 | celery.app.trace       | Task app.task.fourth_debug_task[697eb405-3977-4fee-8287-09767d48bf24] succeeded in 0.00043170599928998854s: None
INFO     | 1  |          |          |          | celery.worker.strategy | Task app.task.fourth_debug_task[41c6afeb-5173-4a1e-bb13-7bb076c4b56b] received
INFO     | 9  | 9a276155 | c7606e5f | 0a17ee29 | celery.app.trace       | Task app.task.third_debug_task[0a17ee29-20c1-43bc-9a0a-da19d5bd90a7] succeeded in 0.0020307229988247855s: None
INFO     | 8  | 9a276155 | 6714d40b | 41c6afeb | app.task               | Debug task 4
INFO     | 9  | 9a276155 | 6714d40b | 5f91f483 | app.task               | Debug task 3
INFO     | 8  | 9a276155 | 6714d40b | 41c6afeb | celery.app.trace       | Task app.task.fourth_debug_task[41c6afeb-5173-4a1e-bb13-7bb076c4b56b] succeeded in 0.00048823299948708154s: None
INFO     | 1  |          |          |          | celery.worker.strategy | Task app.task.fourth_debug_task[e82b49f3-0a0e-4cf7-bcbb-ea3797ec4468] received
INFO     | 9  | 9a276155 | 6714d40b | 5f91f483 | celery.app.trace       | Task app.task.third_debug_task[5f91f483-e28d-4f5b-8eff-304c3e42eb06] succeeded in 0.0017306089994235663s: None
INFO     | 1  |          |          |          | celery.worker.strategy | Task app.task.fourth_debug_task[f2b88702-34a5-4bb8-b18b-dbe6ec133de2] received
INFO     | 9  | 9a276155 | 0a17ee29 | e82b49f3 | app.task               | Debug task 4
INFO     | 8  | 9a276155 | 5f91f483 | f2b88702 | app.task               | Debug task 4
INFO     | 9  | 9a276155 | 0a17ee29 | e82b49f3 | celery.app.trace       | Task app.task.fourth_debug_task[e82b49f3-0a0e-4cf7-bcbb-ea3797ec4468] succeeded in 0.0002958130007755244s: None
INFO     | 8  | 9a276155 | 5f91f483 | f2b88702 | celery.app.trace       | Task app.task.fourth_debug_task[f2b88702-34a5-4bb8-b18b-dbe6ec133de2] succeeded in 0.00036187600017001387s: None
```

<br>

## 4. Advanced Improvements: Addressing Missing Context

### 4-1. Scheduler 的 log 缺乏上下文資訊

Celery 的 Scheduler 在執行 `apply_entry` 時記錄了任務分派訊息，但此時 correlation ID 尚未初始化，導致 log 缺乏上下文。

```python
class Scheduler:
   ...
   def apply_entry(self, entry, producer=None):
       info('Scheduler: Sending due task %s (%s)', entry.name, entry.task)
       try:
           result = self.apply_async(entry, producer=producer, advance=False)
           ...
```

### 4-2. Worker 的 log 與訊號不同步

Celery Worker 在記錄 `LOG_RECEIVED` 後才觸發 `task_received` 訊號，可能導致部分 log 缺乏關鍵上下文。

```python
def default(task, app, consumer,
            info=logger.info, error=logger.error, task_reserved=task_reserved,
            to_system_tz=timezone.to_system, bytes=bytes,
            proto1_to_proto2=proto1_to_proto2):
    ...
    if _does_info:
        context = {
            'id': req.id,
            'name': req.name,
            'args': req.argsrepr,
            'kwargs': req.kwargsrepr,
            'eta': req.eta,
        }
        info(_app_trace.LOG_RECEIVED, context, extra={'data': context})
    ...
    signals.task_received.send(sender=consumer, request=req)
    ...
```

### 解決方法

#### (1) 自訂 log filter，忽略冗餘訊息

```diff
+ class IgnoreSpecificLogFilter(logging.Filter):
+     def filter(self, record):
+         data = getattr(record, 'data', {})
+         if LOG_RECEIVED % {'name': data.get('name'), 'id': data.get('id')} == record.getMessage():
+             return False
+         return True

  @after_setup_logger.connect(weak=False)
  def on_after_setup_logger(logger, *args, **kwargs):
      ...
+     handler.addFilter(IgnoreSpecificLogFilter())
      ...
```

#### (2) 在 Scheduler 和 Worker 關鍵點補充上下文

在任務發布和接收的關鍵時刻重寫 log 記錄邏輯，確保完整性：

```python
@before_task_publish.connect(weak=False)
def on_before_task_publish(headers, properties, **kwargs):
    if properties.get(SCHEDULER_TASK_FLAG_KEY) is True:
        uid = uuid4().hex
        asgi_correlation_id.correlation_id.set(uid)
        headers['CORRELATION_ID'] = uid
        getLogger(__name__).info('Scheduler: Sending due task %s (%s) in @before_task_publish', properties.get(SCHEDULED_TASK_NAME_KEY), headers.get('task'))
        asgi_correlation_id.correlation_id.set(UNSET_ID)

@task_prerun.connect(weak=False)
def on_task_prerun(task, **kwargs):
    if task.request.get('CELERY_PARENT_ID') is None:
        asgi_correlation_id.celery_parent_id.set(UNSET_ID)
    getLogger(__name__).info(LOG_RECEIVED % {'name': task.name,'id': task.request.id} + ' in @task_prerun')
```

<br>

## 5. Results

```diff
         process-id
             |  correlation-id         current-id
             |        |      parent-id      |
             |        |          |          |
+ INFO     | 1  | 3baff0df |          |          | app.celerylogging      | Scheduler: Sending due task test-nested-job (app.task.first_task) in @before_task_publish
+ INFO     | 9  | 3baff0df |          | 65445384 | app.celerylogging      | Task app.task.first_task[65445384-3eec-4494-9403-1bb78dc30cfd] received in in @task_prerun
  INFO     | 9  | 3baff0df |          | 65445384 | app.task               | Debug task 1
  INFO     | 9  | 3baff0df |          | 65445384 | celery.app.trace       | Task app.task.first_task[65445384-3eec-4494-9403-1bb78dc30cfd] succeeded in 0.005659813003148884s: None
+ INFO     | 9  | 3baff0df | 65445384 | 4ff0d138 | app.celerylogging      | Task app.task.second_debug_task[4ff0d138-fd45-4feb-ba9e-62e34c171dd3] received in in @task_prerun
+ INFO     | 8  | 3baff0df | 65445384 | af7b640e | app.celerylogging      | Task app.task.second_debug_task[af7b640e-ed2d-440b-b0a4-c7232cbd3fab] received in in @task_prerun
  INFO     | 9  | 3baff0df | 65445384 | 4ff0d138 | app.task               | Debug task 2
  INFO     | 8  | 3baff0df | 65445384 | af7b640e | app.task               | Debug task 2
  INFO     | 8  | 3baff0df | 65445384 | af7b640e | celery.app.trace       | Task app.task.second_debug_task[af7b640e-ed2d-440b-b0a4-c7232cbd3fab] succeeded in 0.004440903998329304s: None
  INFO     | 9  | 3baff0df | 65445384 | 4ff0d138 | celery.app.trace       | Task app.task.second_debug_task[4ff0d138-fd45-4feb-ba9e-62e34c171dd3] succeeded in 0.004619617000571452s: None
+ INFO     | 9  | 3baff0df | 4ff0d138 | 89815ee9 | app.celerylogging      | Task app.task.third_debug_task[89815ee9-a940-46bf-92c8-a5f5acc1a43f] received in in @task_prerun
+ INFO     | 8  | 3baff0df | af7b640e | d79735d8 | app.celerylogging      | Task app.task.third_debug_task[d79735d8-9816-4222-8320-b146a797b960] received in in @task_prerun
  INFO     | 9  | 3baff0df | 4ff0d138 | 89815ee9 | app.task               | Debug task 3
  INFO     | 8  | 3baff0df | af7b640e | d79735d8 | app.task               | Debug task 3
  INFO     | 8  | 3baff0df | af7b640e | d79735d8 | celery.app.trace       | Task app.task.third_debug_task[d79735d8-9816-4222-8320-b146a797b960] succeeded in 0.002787550001812633s: None
  INFO     | 9  | 3baff0df | 4ff0d138 | 89815ee9 | celery.app.trace       | Task app.task.third_debug_task[89815ee9-a940-46bf-92c8-a5f5acc1a43f] succeeded in 0.002928071000496857s: None
+ INFO     | 9  | 3baff0df | af7b640e | 2bd2d543 | app.celerylogging      | Task app.task.fourth_debug_task[2bd2d543-19e2-43ed-8aa9-9478157d9ad8] received in in @task_prerun
+ INFO     | 8  | 3baff0df | 4ff0d138 | 2740f5cf | app.celerylogging      | Task app.task.fourth_debug_task[2740f5cf-6d5c-4d0a-a2da-53b5c75bc365] received in in @task_prerun
  INFO     | 9  | 3baff0df | af7b640e | 2bd2d543 | app.task               | Debug task 4
  INFO     | 8  | 3baff0df | 4ff0d138 | 2740f5cf | app.task               | Debug task 4
  INFO     | 9  | 3baff0df | af7b640e | 2bd2d543 | celery.app.trace       | Task app.task.fourth_debug_task[2bd2d543-19e2-43ed-8aa9-9478157d9ad8] succeeded in 0.0005955449960310943s: None
  INFO     | 8  | 3baff0df | 4ff0d138 | 2740f5cf | celery.app.trace       | Task app.task.fourth_debug_task[2740f5cf-6d5c-4d0a-a2da-53b5c75bc365] succeeded in 0.0009539919992676005s: None
+ INFO     | 9  | 3baff0df | d79735d8 | f5bf3ed7 | app.celerylogging      | Task app.task.fourth_debug_task[f5bf3ed7-480e-4b07-8c41-683ce391eb10] received in in @task_prerun
+ INFO     | 8  | 3baff0df | 89815ee9 | cb6d30cc | app.celerylogging      | Task app.task.fourth_debug_task[cb6d30cc-769e-4491-ac37-d346ca870c27] received in in @task_prerun
  INFO     | 8  | 3baff0df | 89815ee9 | cb6d30cc | app.task               | Debug task 4
  INFO     | 9  | 3baff0df | d79735d8 | f5bf3ed7 | app.task               | Debug task 4
  INFO     | 8  | 3baff0df | 89815ee9 | cb6d30cc | celery.app.trace       | Task app.task.fourth_debug_task[cb6d30cc-769e-4491-ac37-d346ca870c27] succeeded in 0.0008838119974825531s: None
  INFO     | 9  | 3baff0df | d79735d8 | f5bf3ed7 | celery.app.trace       | Task app.task.fourth_debug_task[f5bf3ed7-480e-4b07-8c41-683ce391eb10] succeeded in 0.0009317440053564496s: None
```

