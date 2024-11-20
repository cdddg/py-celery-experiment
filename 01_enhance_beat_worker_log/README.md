# Improving Celery Task Log Traceability

這篇紀錄旨在探討如何提升 Celery 記錄的可追蹤性和閱讀性，讓管理和除錯過程更為高效。

<br>

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
   correlation-id          current-id
         |      parent-id      |
         |          |          |
INFO [        ] [        ] [        ] celery.beat            | Scheduler: Sending due task test-nested-job (app.task.first_task)
INFO [        ] [        ] [        ] celery.worker.strategy | Task app.task.first_task[ea2e59f9-b293-4d64-bf65-f5125ebb97e1] received
INFO [95382411] [        ] [ea2e59f9] app.task               | Debug task 1
INFO [        ] [        ] [        ] celery.worker.strategy | Task app.task.second_debug_task[09c23ded-8393-4951-9a03-42fffc830d17] received
INFO [        ] [        ] [        ] celery.worker.strategy | Task app.task.second_debug_task[81407a8c-9c54-4538-acb3-a08fe5dde561] received
INFO [95382411] [        ] [ea2e59f9] celery.app.trace       | Task app.task.first_task[ea2e59f9-b293-4d64-bf65-f5125ebb97e1] succeeded in 0.03319657999963965s: None
INFO [95382411] [ea2e59f9] [09c23ded] app.task               | Debug task 2
INFO [        ] [        ] [        ] celery.worker.strategy | Task app.task.third_debug_task[250b8b2e-1a84-409b-ac2a-14bb953bfff3] received
INFO [95382411] [ea2e59f9] [09c23ded] celery.app.trace       | Task app.task.second_debug_task[09c23ded-8393-4951-9a03-42fffc830d17] succeeded in 0.00590658700093627s: None
INFO [        ] [        ] [        ] celery.worker.strategy | Task app.task.fourth_debug_task[461aac43-2619-48fa-8507-6942f56dc4aa] received
INFO [95382411] [ea2e59f9] [81407a8c] app.task               | Debug task 2
INFO [        ] [        ] [        ] celery.worker.strategy | Task app.task.third_debug_task[5995d3e8-a378-410d-b83b-6f1b23e8bb10] received
INFO [95382411] [ea2e59f9] [81407a8c] celery.app.trace       | Task app.task.second_debug_task[81407a8c-9c54-4538-acb3-a08fe5dde561] succeeded in 0.006049554001947399s: None
INFO [        ] [        ] [        ] celery.worker.strategy | Task app.task.fourth_debug_task[d10f49d0-2ee4-480c-9d9b-0bdbb9ea4c23] received
INFO [95382411] [09c23ded] [250b8b2e] app.task               | Debug task 3
INFO [        ] [        ] [        ] celery.worker.strategy | Task app.task.fourth_debug_task[5e1f8022-89d5-432a-a674-10b29be0a557] received
INFO [95382411] [09c23ded] [250b8b2e] celery.app.trace       | Task app.task.third_debug_task[250b8b2e-1a84-409b-ac2a-14bb953bfff3] succeeded in 0.0036318539932835847s: None
INFO [95382411] [09c23ded] [461aac43] app.task               | Debug task 4
INFO [95382411] [09c23ded] [461aac43] celery.app.trace       | Task app.task.fourth_debug_task[461aac43-2619-48fa-8507-6942f56dc4aa] succeeded in 0.002018771003349684s: None
INFO [95382411] [81407a8c] [5995d3e8] app.task               | Debug task 3
INFO [        ] [        ] [        ] celery.worker.strategy | Task app.task.fourth_debug_task[f1dbfa52-9177-4ceb-a0fe-a00ce8a19de1] received
INFO [95382411] [81407a8c] [5995d3e8] celery.app.trace       | Task app.task.third_debug_task[5995d3e8-a378-410d-b83b-6f1b23e8bb10] succeeded in 0.0035413389996392652s: None
INFO [95382411] [81407a8c] [d10f49d0] app.task               | Debug task 4
INFO [95382411] [81407a8c] [d10f49d0] celery.app.trace       | Task app.task.fourth_debug_task[d10f49d0-2ee4-480c-9d9b-0bdbb9ea4c23] succeeded in 0.001998387997446116s: None
INFO [95382411] [250b8b2e] [5e1f8022] app.task               | Debug task 4
INFO [95382411] [250b8b2e] [5e1f8022] celery.app.trace       | Task app.task.fourth_debug_task[5e1f8022-89d5-432a-a674-10b29be0a557] succeeded in 0.0019207799996365793s: None
INFO [95382411] [5995d3e8] [f1dbfa52] app.task               | Debug task 4
INFO [95382411] [5995d3e8] [f1dbfa52] celery.app.trace       | Task app.task.fourth_debug_task[f1dbfa52-9177-4ceb-a0fe-a00ce8a19de1] succeeded in 0.0017463759941165335s: None
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
      correlation-id          current-id
            |      parent-id      |
            |          |          |
+ INFO [95382411] [        ] [        ] app.celerylogging      | Scheduler: Sending due task test-nested-job (app.task.first_task) in @before_task_publish
+ INFO [95382411] [        ] [ea2e59f9] app.celerylogging      | Task app.task.first_task[ea2e59f9-b293-4d64-bf65-f5125ebb97e1] received in @task_prerun
  INFO [95382411] [        ] [ea2e59f9] app.task               | Debug task 1
+ INFO [95382411] [ea2e59f9] [09c23ded] celery.worker.strategy | Task app.task.second_debug_task[09c23ded-8393-4951-9a03-42fffc830d17] received in @task_prerun
+ INFO [95382411] [ea2e59f9] [81407a8c] celery.worker.strategy | Task app.task.second_debug_task[81407a8c-9c54-4538-acb3-a08fe5dde561] received in @task_prerun
  INFO [95382411] [        ] [ea2e59f9] celery.app.trace       | Task app.task.first_task[ea2e59f9-b293-4d64-bf65-f5125ebb97e1] succeeded in 0.03319657999963965s: None
  INFO [95382411] [ea2e59f9] [09c23ded] app.task               | Debug task 2
...
```



