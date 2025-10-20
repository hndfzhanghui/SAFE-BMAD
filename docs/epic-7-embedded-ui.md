# Epic 7: 嵌入式界面和高级功能

## 概述

Epic 7 负责开发嵌入式界面组件和完善的高级功能，支持SAFE系统与现有系统的深度集成。通过轻量级、可嵌入的界面组件，使SAFE的智能分析能力能够无缝集成到SIMAP等其他系统中，同时提供高级数据可视化、用户体验优化和移动端支持等功能。

## 目标与价值

### 核心目标
- 开发轻量级、可嵌入的界面组件库
- 实现与现有系统的无缝集成体验
- 提供高级数据可视化和分析功能
- 优化用户体验和系统响应性能
- 支持移动端和多设备适配

### 业务价值
- **集成便利**: 降低系统集成门槛，提升部署灵活性
- **用户体验**: 提供更加直观和高效的分析界面
- **功能增强**: 通过高级功能提升决策支持能力
- **移动支持**: 满足现场移动办公和应急指挥需求

## 嵌入式组件架构

### 组件架构设计

```
嵌入式组件系统
├── 核心组件库
│   ├── 智能分析卡片组件
│   ├── 决策建议浮窗组件
│   ├── Agent状态指示器
│   ├── 快速操作面板
│   └── 数据可视化组件
├── 集成适配层
│   ├── SIMAP集成适配器
│   ├── 通用系统集成器
│   ├── 主题样式适配器
│   └── 数据接口适配器
├── 高级功能模块
│   ├── 高级数据可视化
│   ├── 交互式分析工具
│   ├── 智能推荐系统
│   └── 协作分析功能
└── 移动端支持
    ├── 响应式设计
    ├── 移动端优化
    ├── 离线模式支持
    └── 原生应用集成
```

### 组件设计原则

#### 1. 轻量级设计
- 组件体积小，加载快速
- 依赖最小化，按需加载
- 内存占用低，性能优异
- 支持Tree Shaking优化

#### 2. 高度可配置
- 丰富的配置选项
- 灵活的主题定制
- 可扩展的事件系统
- 支持多种集成方式

#### 3. 无缝集成
- 标准化的接口规范
- 兼容主流框架和库
- 最小化侵入式集成
- 良好的隔离性设计

## 详细功能设计

### 7.1 核心嵌入式组件

#### 7.1.1 智能分析卡片组件
**优先级**: P0 (最高)

**功能描述**:
- 轻量级的分析结果展示组件
- 支持多种分析类型和数据格式
- 提供丰富的交互和自定义选项
- 确保在不同环境下的视觉一致性

**组件设计**:
```typescript
interface SmartAnalysisCardProps {
  // 基础配置
  analysisType: 's-agent' | 'a-agent' | 'f-agent' | 'e-agent' | 'comprehensive';
  data: AnalysisData;
  config?: CardConfig;

  // 样式配置
  theme?: 'light' | 'dark' | 'auto';
  size?: 'small' | 'medium' | 'large';
  variant?: 'default' | 'compact' | 'detailed';

  // 交互配置
  interactive?: boolean;
  expandable?: boolean;
  showDetails?: boolean;

  // 事件回调
  onClick?: (data: AnalysisData) => void;
  onExpand?: (expanded: boolean) => void;
  onAction?: (action: string, data: any) => void;

  // 集成配置
  locale?: string;
  apiUrl?: string;
  authToken?: string;
}

const SmartAnalysisCard: React.FC<SmartAnalysisCardProps> = ({
  analysisType,
  data,
  config = {},
  theme = 'auto',
  size = 'medium',
  variant = 'default',
  interactive = true,
  expandable = true,
  showDetails = false,
  onClick,
  onExpand,
  onAction,
  locale = 'zh-CN',
  apiUrl,
  authToken
}) => {
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 主题检测和应用
  const resolvedTheme = useTheme(theme);

  // 数据格式化
  const formattedData = useFormattedData(data, analysisType, locale);

  // 卡片样式
  const cardStyles = useCardStyles(size, variant, resolvedTheme);

  const handleCardClick = useCallback(() => {
    if (interactive && onClick) {
      onClick(data);
    }
    if (expandable) {
      const newExpanded = !expanded;
      setExpanded(newExpanded);
      onExpand?.(newExpanded);
    }
  }, [interactive, onClick, expandable, expanded, onExpand]);

  const handleAction = useCallback(async (action: string, actionData: any) => {
    try {
      setLoading(true);
      setError(null);

      if (onAction) {
        await onAction(action, actionData);
      } else {
        // 默认动作处理
        await handleDefaultAction(action, actionData, apiUrl, authToken);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [onAction, apiUrl, authToken]);

  return (
    <Card
      className={clsx(
        'safe-analysis-card',
        `safe-analysis-card--${analysisType}`,
        `safe-analysis-card--${size}`,
        `safe-analysis-card--${variant}`,
        {
          'safe-analysis-card--interactive': interactive,
          'safe-analysis-card--expanded': expanded,
          'safe-analysis-card--loading': loading
        }
      )}
      style={cardStyles.container}
      onClick={handleCardClick}
    >
      {/* 卡片头部 */}
      <CardHeader className="safe-analysis-card__header">
        <div className="safe-analysis-card__title">
          <AgentIcon type={analysisType} />
          <span>{getAgentTitle(analysisType, locale)}</span>
        </div>
        <div className="safe-analysis-card__meta">
          <Badge
            status={data.status}
            text={getStatusText(data.status, locale)}
          />
          <span className="safe-analysis-card__timestamp">
            {formatTimestamp(data.timestamp, locale)}
          </span>
        </div>
      </CardHeader>

      {/* 卡片内容 */}
      <CardBody className="safe-analysis-card__body">
        {error && (
          <Alert
            type="error"
            message={error}
            closable
            onClose={() => setError(null)}
          />
        )}

        {loading && <LoadingSpinner />}

        {!loading && !error && (
          <>
            {/* 核心指标展示 */}
            <div className="safe-analysis-card__metrics">
              {renderKeyMetrics(formattedData, analysisType, variant)}
            </div>

            {/* 关键发现 */}
            {data.keyFindings && data.keyFindings.length > 0 && (
              <div className="safe-analysis-card__findings">
                <h4>关键发现</h4>
                <ul>
                  {data.keyFindings.map((finding, index) => (
                    <li key={index}>{finding}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* 详细内容（展开时显示） */}
            {expanded && showDetails && (
              <div className="safe-analysis-card__details">
                {renderDetailedContent(formattedData, analysisType)}
              </div>
            )}
          </>
        )}
      </CardBody>

      {/* 卡片操作栏 */}
      {interactive && (
        <CardFooter className="safe-analysis-card__footer">
          <div className="safe-analysis-card__actions">
            {renderActionButtons(data, analysisType, handleAction)}
          </div>
          {expandable && (
            <Button
              type="text"
              size="small"
              icon={expanded ? <UpOutlined /> : <DownOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                handleCardClick();
              }}
            />
          )}
        </CardFooter>
      )}
    </Card>
  );
};

// 组件使用示例
const ExampleUsage: React.FC = () => {
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);

  useEffect(() => {
    // 获取分析数据
    fetchAnalysisData().then(setAnalysisData);
  }, []);

  const handleCardClick = (data: AnalysisData) => {
    console.log('卡片被点击:', data);
  };

  const handleCardAction = async (action: string, actionData: any) => {
    console.log('卡片操作:', action, actionData);
  };

  return (
    <div className="embedded-components-demo">
      {/* S-Agent分析卡片 */}
      <SmartAnalysisCard
        analysisType="s-agent"
        data={analysisData}
        size="medium"
        variant="default"
        interactive
        expandable
        onClick={handleCardClick}
        onAction={handleCardAction}
      />

      {/* A-Agent分析卡片 - 紧凑版 */}
      <SmartAnalysisCard
        analysisType="a-agent"
        data={analysisData}
        size="small"
        variant="compact"
        theme="dark"
      />

      {/* 综合分析卡片 - 详细版 */}
      <SmartAnalysisCard
        analysisType="comprehensive"
        data={analysisData}
        size="large"
        variant="detailed"
        showDetails
        interactive
        expandable
      />
    </div>
  );
};
```

#### 7.1.2 决策建议浮窗组件
**优先级**: P0 (最高)

**功能描述**:
- 轻量级的决策建议展示组件
- 支持浮窗、模态框等多种展示模式
- 提供建议详情和执行追踪功能
- 支持用户反馈和评估机制

**组件设计**:
```typescript
interface DecisionRecommendationProps {
  // 建议数据
  recommendations: Recommendation[];
  currentContext: DecisionContext;

  // 展示配置
  mode?: 'floating' | 'modal' | 'inline' | 'sidebar';
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  trigger?: 'click' | 'hover' | 'auto';

  // 功能配置
  showDetails?: boolean;
  allowFeedback?: boolean;
  showConfidence?: boolean;
  trackExecution?: boolean;

  // 样式配置
  theme?: Theme;
  size?: Size;
  customStyles?: CSSProperties;

  // 事件回调
  onAccept?: (recommendation: Recommendation) => void;
  onReject?: (recommendation: Recommendation, reason: string) => void;
  onFeedback?: (recommendation: Recommendation, feedback: Feedback) => void;
}

const DecisionRecommendation: React.FC<DecisionRecommendationProps> = ({
  recommendations,
  currentContext,
  mode = 'floating',
  position = 'top-right',
  trigger = 'auto',
  showDetails = true,
  allowFeedback = true,
  showConfidence = true,
  trackExecution = true,
  theme = 'light',
  size = 'medium',
  customStyles,
  onAccept,
  onReject,
  onFeedback
}) => {
  const [visible, setVisible] = useState(false);
  const [selectedRecommendation, setSelectedRecommendation] = useState<Recommendation | null>(null);
  const [feedbackMode, setFeedbackMode] = useState(false);
  const [executionTracking, setExecutionTracking] = useState<ExecutionTracker | null>(null);

  // 自动显示逻辑
  useEffect(() => {
    if (trigger === 'auto' && recommendations.length > 0) {
      const hasHighPriority = recommendations.some(r => r.priority === 'high');
      const hasNewRecommendations = recommendations.some(r => r.isNew);

      if (hasHighPriority || hasNewRecommendations) {
        setVisible(true);
      }
    }
  }, [recommendations, trigger]);

  const handleAcceptRecommendation = async (recommendation: Recommendation) => {
    try {
      // 记录执行跟踪
      if (trackExecution) {
        const tracker = new ExecutionTracker(recommendation);
        setExecutionTracking(tracker);
        await tracker.start();
      }

      // 调用回调
      if (onAccept) {
        await onAccept(recommendation);
      }

      // 更新建议状态
      recommendation.status = 'accepted';
      recommendation.acceptedAt = new Date();

    } catch (error) {
      console.error('接受建议失败:', error);
    }
  };

  const handleRejectRecommendation = async (recommendation: Recommendation, reason: string) => {
    try {
      // 调用回调
      if (onReject) {
        await onReject(recommendation, reason);
      }

      // 更新建议状态
      recommendation.status = 'rejected';
      recommendation.rejectedAt = new Date();
      recommendation.rejectionReason = reason;

    } catch (error) {
      console.error('拒绝建议失败:', error);
    }
  };

  const handleFeedback = async (recommendation: Recommendation, feedback: Feedback) => {
    try {
      // 调用回调
      if (onFeedback) {
        await onFeedback(recommendation, feedback);
      }

      // 更新建议
      recommendation.feedback = feedback;
      recommendation.hasFeedback = true;

      setFeedbackMode(false);

    } catch (error) {
      console.error('提交反馈失败:', error);
    }
  };

  const renderRecommendationContent = (recommendation: Recommendation) => (
    <div className="recommendation-content">
      {/* 建议头部 */}
      <div className="recommendation-header">
        <div className="recommendation-title">
          <h3>{recommendation.title}</h3>
          <div className="recommendation-meta">
            <Badge
              status={getPriorityStatus(recommendation.priority)}
              text={getPriorityText(recommendation.priority)}
            />
            {showConfidence && (
              <span className="confidence-score">
                置信度: {Math.round(recommendation.confidence * 100)}%
              </span>
            )}
          </div>
        </div>
        <div className="recommendation-actions">
          <Button
            type="primary"
            size="small"
            onClick={() => handleAcceptRecommendation(recommendation)}
            disabled={recommendation.status === 'accepted'}
          >
            采纳
          </Button>
          <Button
            size="small"
            onClick={() => {
              setSelectedRecommendation(recommendation);
              setFeedbackMode(true);
            }}
          >
            拒绝
          </Button>
        </div>
      </div>

      {/* 建议内容 */}
      <div className="recommendation-body">
        <p className="recommendation-description">{recommendation.description}</p>

        {/* 详细信息 */}
        {showDetails && recommendation.details && (
          <div className="recommendation-details">
            <Collapse>
              <Panel header="详细信息" key="details">
                <div dangerouslySetInnerHTML={{ __html: recommendation.details }} />
              </Panel>
            </Collapse>
          </div>
        )}

        {/* 执行步骤 */}
        {recommendation.executionSteps && (
          <div className="recommendation-steps">
            <h4>执行步骤</h4>
            <Steps
              direction="vertical"
              size="small"
              current={executionTracking?.currentStep || 0}
            >
              {recommendation.executionSteps.map((step, index) => (
                <Step
                  key={index}
                  title={step.title}
                  description={step.description}
                  status={getStepStatus(index, executionTracking)}
                />
              ))}
            </Steps>
          </div>
        )}

        {/* 预期效果 */}
        {recommendation.expectedOutcomes && (
          <div className="recommendation-outcomes">
            <h4>预期效果</h4>
            <ul>
              {recommendation.expectedOutcomes.map((outcome, index) => (
                <li key={index}>{outcome}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* 反馈区域 */}
      {allowFeedback && feedbackMode && selectedRecommendation?.id === recommendation.id && (
        <FeedbackForm
          recommendation={recommendation}
          onSubmit={(feedback) => handleFeedback(recommendation, feedback)}
          onCancel={() => setFeedbackMode(false)}
        />
      )}
    </div>
  );

  // 渲染不同模式的组件
  if (mode === 'floating') {
    return (
      <FloatButton
        icon={<NotificationOutlined />}
        badge={{ count: recommendations.length }}
        style={{
          position: 'fixed',
          [position.replace('-', '-')]: 24,
          ...customStyles
        }}
        onClick={() => setVisible(!visible)}
      >
        <Drawer
          title="决策建议"
          placement="right"
          onClose={() => setVisible(false)}
          open={visible}
          width={400}
        >
          <div className="recommendations-list">
            {recommendations.map(recommendation => (
              <Card key={recommendation.id} className="recommendation-card">
                {renderRecommendationContent(recommendation)}
              </Card>
            ))}
          </div>
        </Drawer>
      </FloatButton>
    );
  }

  if (mode === 'modal') {
    return (
      <Modal
        title="决策建议"
        open={visible}
        onCancel={() => setVisible(false)}
        footer={null}
        width={600}
      >
        <div className="recommendations-list">
          {recommendations.map(recommendation => (
            <Card key={recommendation.id} className="recommendation-card">
              {renderRecommendationContent(recommendation)}
            </Card>
          ))}
        </div>
      </Modal>
    );
  }

  if (mode === 'inline') {
    return (
      <div className="recommendations-inline" style={customStyles}>
        {recommendations.map(recommendation => (
          <Card key={recommendation.id} className="recommendation-card">
            {renderRecommendationContent(recommendation)}
          </Card>
        ))}
      </div>
    );
  }

  return null;
};

// 反馈表单组件
const FeedbackForm: React.FC<FeedbackFormProps> = ({
  recommendation,
  onSubmit,
  onCancel
}) => {
  const [form] = Form.useForm();

  const handleSubmit = async (values: any) => {
    const feedback: Feedback = {
      recommendationId: recommendation.id,
      rating: values.rating,
      comment: values.comment,
      reasons: values.reasons,
      timestamp: new Date(),
      userAgent: navigator.userAgent
    };

    await onSubmit(feedback);
    form.resetFields();
  };

  return (
    <Card className="feedback-form">
      <h4>建议反馈</h4>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        <Form.Item
          name="rating"
          label="建议评分"
          rules={[{ required: true, message: '请选择评分' }]}
        >
          <Rate />
        </Form.Item>

        <Form.Item
          name="reasons"
          label="拒绝原因"
          rules={[{ required: true, message: '请选择拒绝原因' }]}
        >
          <Checkbox.Group>
            <Checkbox value="not_applicable">不符合当前情况</Checkbox>
            <Checkbox value="lack_resources">缺乏必要资源</Checkbox>
            <Checkbox value="time_constraints">时间不允许</Checkbox>
            <Checkbox value="better_alternative">有更好的方案</Checkbox>
            <Checkbox value="other">其他原因</Checkbox>
          </Checkbox.Group>
        </Form.Item>

        <Form.Item
          name="comment"
          label="详细说明"
        >
          <TextArea rows={3} placeholder="请详细说明您的想法..." />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">
              提交反馈
            </Button>
            <Button onClick={onCancel}>
              取消
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};
```

#### 7.1.3 Agent状态指示器
**优先级**: P1 (高)

**功能描述**:
- 实时显示各Agent的工作状态
- 提供详细的性能和健康指标
- 支持状态变化的通知和告警
- 确保用户对系统状态的清晰了解

**组件设计**:
```typescript
interface AgentStatusIndicatorProps {
  // 配置选项
  agents: AgentStatus[];
  layout?: 'horizontal' | 'vertical' | 'grid';
  size?: 'small' | 'medium' | 'large';
  showDetails?: boolean;
  realTime?: boolean;

  // 样式配置
  theme?: Theme;
  position?: 'fixed' | 'static';
  customStyles?: CSSProperties;

  // 功能配置
  allowDrillDown?: boolean;
  showMetrics?: boolean;
  enableAlerts?: boolean;

  // 事件回调
  onStatusChange?: (agentId: string, oldStatus: string, newStatus: string) => void;
  onAgentClick?: (agent: AgentStatus) => void;
}

const AgentStatusIndicator: React.FC<AgentStatusIndicatorProps> = ({
  agents,
  layout = 'horizontal',
  size = 'medium',
  showDetails = false,
  realTime = true,
  theme = 'light',
  position = 'static',
  customStyles,
  allowDrillDown = true,
  showMetrics = true,
  enableAlerts = true,
  onStatusChange,
  onAgentClick
}) => {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [agentDetails, setAgentDetails] = useState<Record<string, AgentDetails>>({});

  // 实时状态更新
  useEffect(() => {
    if (!realTime) return;

    const interval = setInterval(async () => {
      try {
        const updatedAgents = await fetchAgentStatuses();

        // 检测状态变化
        updatedAgents.forEach(updatedAgent => {
          const oldAgent = agents.find(a => a.id === updatedAgent.id);
          if (oldAgent && oldAgent.status !== updatedAgent.status) {
            onStatusChange?.(updatedAgent.id, oldAgent.status, updatedAgent.status);
          }
        });

      } catch (error) {
        console.error('获取Agent状态失败:', error);
      }
    }, 5000); // 5秒更新一次

    return () => clearInterval(interval);
  }, [realTime, agents, onStatusChange]);

  // 获取Agent详细信息
  const handleAgentClick = async (agent: AgentStatus) => {
    if (!allowDrillDown) return;

    setSelectedAgent(agent.id);

    if (!agentDetails[agent.id]) {
      try {
        const details = await fetchAgentDetails(agent.id);
        setAgentDetails(prev => ({
          ...prev,
          [agent.id]: details
        }));
      } catch (error) {
        console.error('获取Agent详情失败:', error);
      }
    }

    onAgentClick?.(agent);
  };

  const renderAgentIndicator = (agent: AgentStatus) => {
    const statusColor = getStatusColor(agent.status);
    const statusText = getStatusText(agent.status);
    const details = agentDetails[agent.id];

    return (
      <div
        key={agent.id}
        className={clsx(
          'agent-indicator',
          `agent-indicator--${size}`,
          `agent-indicator--${agent.status}`,
          {
            'agent-indicator--selected': selectedAgent === agent.id,
            'agent-indicator--clickable': allowDrillDown
          }
        )}
        onClick={() => handleAgentClick(agent)}
      >
        {/* Agent基本信息 */}
        <div className="agent-indicator__basic">
          <div className="agent-indicator__icon">
            <AgentIcon type={agent.type} status={agent.status} />
          </div>
          <div className="agent-indicator__info">
            <div className="agent-indicator__name">
              {agent.displayName}
            </div>
            <div className="agent-indicator__status">
              <Badge
                color={statusColor}
                text={statusText}
              />
            </div>
          </div>
          <div className="agent-indicator__metrics">
            {showMetrics && (
              <div className="agent-metrics">
                <div className="metric-item">
                  <span className="metric-label">CPU</span>
                  <span className="metric-value">{agent.metrics.cpu}%</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">内存</span>
                  <span className="metric-value">{agent.metrics.memory}%</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">响应</span>
                  <span className="metric-value">{agent.metrics.responseTime}ms</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 详细信息（展开时显示） */}
        {selectedAgent === agent.id && details && (
          <div className="agent-indicator__details">
            <div className="details-section">
              <h5>性能指标</h5>
              <div className="metrics-grid">
                <div className="metric">
                  <span className="metric-name">处理任务数</span>
                  <span className="metric-value">{details.processedTasks}</span>
                </div>
                <div className="metric">
                  <span className="metric-name">成功率</span>
                  <span className="metric-value">{details.successRate}%</span>
                </div>
                <div className="metric">
                  <span className="metric-name">平均处理时间</span>
                  <span className="metric-value">{details.avgProcessingTime}s</span>
                </div>
                <div className="metric">
                  <span className="metric-name">队列长度</span>
                  <span className="metric-value">{details.queueLength}</span>
                </div>
              </div>
            </div>

            <div className="details-section">
              <h5>最近活动</h5>
              <Timeline size="small">
                {details.recentActivities.map((activity, index) => (
                  <Timeline.Item key={index}>
                    <div className="activity-item">
                      <div className="activity-type">{activity.type}</div>
                      <div className="activity-description">{activity.description}</div>
                      <div className="activity-time">
                        {formatRelativeTime(activity.timestamp)}
                      </div>
                    </div>
                  </Timeline.Item>
                ))}
              </Timeline>
            </div>

            {details.errors && details.errors.length > 0 && (
              <div className="details-section">
                <h5>最近错误</h5>
                <Alert
                  type="error"
                  message="检测到错误"
                  description={
                    <ul>
                      {details.errors.slice(0, 3).map((error, index) => (
                        <li key={index}>{error.message}</li>
                      ))}
                    </ul>
                  }
                />
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const containerClasses = clsx(
    'agent-status-indicator',
    `agent-status-indicator--${layout}`,
    `agent-status-indicator--${size}`,
    `agent-status-indicator--${position}`,
    {
      'agent-status-indicator--realtime': realTime
    }
  );

  return (
    <div
      className={containerClasses}
      style={customStyles}
    >
      <div className="agent-status-indicator__header">
        <h4>Agent状态监控</h4>
        {realTime && (
          <div className="realtime-indicator">
            <div className="realtime-dot" />
            <span>实时</span>
          </div>
        )}
      </div>

      <div className="agent-status-indicator__content">
        {layout === 'horizontal' && (
          <div className="agents-horizontal">
            {agents.map(renderAgentIndicator)}
          </div>
        )}

        {layout === 'vertical' && (
          <div className="agents-vertical">
            {agents.map(renderAgentIndicator)}
          </div>
        )}

        {layout === 'grid' && (
          <div className="agents-grid">
            {agents.map(renderAgentIndicator)}
          </div>
        )}
      </div>

      {/* 状态汇总 */}
      <div className="agent-status-indicator__summary">
        <div className="summary-item">
          <span className="summary-label">运行中</span>
          <span className="summary-value">
            {agents.filter(a => a.status === 'running').length}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">空闲</span>
          <span className="summary-value">
            {agents.filter(a => a.status === 'idle').length}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">错误</span>
          <span className="summary-value">
            {agents.filter(a => a.status === 'error').length}
          </span>
        </div>
      </div>
    </div>
  );
};
```

### 7.2 高级数据可视化

#### 7.2.1 交互式态势地图
**优先级**: P1 (高)

**功能描述**:
- 基于WebGL的高性能地图渲染
- 支持多图层动态叠加和交互
- 提供丰富的地图分析工具
- 支持实时数据更新和动画效果

**技术实现**:
```typescript
class InteractiveSituationMap {
  private mapInstance: Map;
  private layerManager: LayerManager;
  private interactionManager: InteractionManager;
  private animationEngine: AnimationEngine;

  constructor(container: HTMLElement, config: MapConfig) {
    this.initializeMap(container, config);
    this.setupLayerManager();
    this.setupInteractions();
    this.setupAnimationEngine();
  }

  private initializeMap(container: HTMLElement, config: MapConfig) {
    this.mapInstance = new Map({
      container: container,
      style: config.mapStyle,
      center: config.center,
      zoom: config.zoom,
      pitch: config.pitch,
      bearing: config.bearing
    });

    // 添加控制器
    this.mapInstance.addControl(new NavigationControl());
    this.mapInstance.addControl(new ScaleControl());
  }

  // 添加态势分析图层
  addSituationAnalysisLayer(data: SituationAnalysisData): string {
    const layerId = `situation-${Date.now()}`;

    // 影响区域图层
    this.mapInstance.addLayer({
      id: `${layerId}-affected-areas`,
      type: 'fill',
      source: {
        type: 'geojson',
        data: data.affectedAreas
      },
      paint: {
        'fill-color': [
          'interpolate',
          ['linear'],
          ['get', 'severity'],
          1, '#ffeda0',
          2, '#fed976',
          3, '#feb24c',
          4, '#fd8d3c',
          5, '#fc4e2a',
          6, '#e31a1c',
          7, '#bd0026',
          8, '#800026'
        ],
        'fill-opacity': 0.7
      }
    });

    // 热力图图层
    this.mapInstance.addLayer({
      id: `${layerId}-heatmap`,
      type: 'heatmap',
      source: {
        type: 'geojson',
        data: data.activityPoints
      },
      paint: {
        'heatmap-weight': [
          'interpolate',
          ['linear'],
          ['get', 'intensity'],
          0, 0,
          6, 1
        ],
        'heatmap-intensity': [
          'interpolate',
          ['linear'],
          ['zoom'],
          0, 1,
          15, 3
        ],
        'heatmap-color': [
          'interpolate',
          ['linear'],
          ['heatmap-density'],
          0, 'rgba(33,102,172,0)',
          0.2, 'rgb(103,169,207)',
          0.4, 'rgb(209,229,240)',
          0.6, 'rgb(253,219,199)',
          0.8, 'rgb(239,138,98)',
          1, 'rgb(178,24,43)'
        ],
        'heatmap-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          0, 2,
          15, 20
        ]
      }
    });

    // 动态轨迹图层
    this.mapInstance.addLayer({
      id: `${layerId}-trajectories`,
      type: 'line',
      source: {
        type: 'geojson',
        data: data.trajectories
      },
      paint: {
        'line-color': '#3b82f6',
        'line-width': 3,
        'line-opacity': 0.8
      },
      layout: {
        'line-cap': 'round',
        'line-join': 'round'
      }
    });

    return layerId;
  }

  // 添加救援资源图层
  addResourceLayer(resources: ResourceData[]): string {
    const layerId = `resources-${Date.now()}`;

    // 资源点图层
    this.mapInstance.addLayer({
      id: `${layerId}-resource-points`,
      type: 'symbol',
      source: {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: resources.map(resource => ({
            type: 'Feature',
            geometry: {
              type: 'Point',
              coordinates: [resource.location.lng, resource.location.lat]
            },
            properties: {
              id: resource.id,
              type: resource.type,
              name: resource.name,
              status: resource.status,
              capacity: resource.capacity,
              currentLoad: resource.currentLoad
            }
          }))
        }
      },
      layout: {
        'icon-image': [
          'match',
          ['get', 'type'],
          'rescue_team', 'rescue-team-icon',
          'medical', 'medical-icon',
          'shelter', 'shelter-icon',
          'supplies', 'supplies-icon',
          'default-icon'
        ],
        'icon-size': 1.2,
        'text-field': ['get', 'name'],
        'text-font': ['Open Sans Regular'],
        'text-offset': [0, 1.5],
        'text-anchor': 'top'
      },
      paint: {
        'text-color': '#333333',
        'text-halo-color': '#ffffff',
        'text-halo-width': 1
      }
    });

    return layerId;
  }

  // 添加实时数据动画
  animateRealTimeData(dataStream: RealTimeDataStream) {
    const animationId = `animation-${Date.now()}`;

    this.animationEngine.startAnimation(animationId, {
      duration: 5000, // 5秒动画
      update: (progress: number) => {
        // 更新数据点位置
        const updatedFeatures = dataStream.points.map(point => ({
          ...point,
          geometry: {
            ...point.geometry,
            coordinates: this.interpolatePosition(
              point.from,
              point.to,
              progress
            )
          }
        }));

        // 更新地图源数据
        this.mapInstance.getSource(`${animationId}-points`)?.setData({
          type: 'FeatureCollection',
          features: updatedFeatures
        });
      },
      onComplete: () => {
        console.log('动画完成');
      }
    });
  }

  // 设置交互工具
  setupAnalysisTools() {
    // 测量工具
    const measureTool = new MeasureTool(this.mapInstance);

    // 绘制工具
    const drawTool = new DrawTool(this.mapInstance, {
      modes: ['draw_point', 'draw_line_string', 'draw_polygon']
    });

    // 缓冲区分析工具
    const bufferTool = new BufferAnalysisTool(this.mapInstance);

    // 视域分析工具
    const viewshedTool = new ViewshedAnalysisTool(this.mapInstance);

    return {
      measureTool,
      drawTool,
      bufferTool,
      viewshedTool
    };
  }

  // 添加3D可视化
  add3DVisualization(data: ThreeDData) {
    // 启用3D地形
    this.mapInstance.addSource('terrain', {
      type: 'raster-dem',
      url: 'mapbox://mapbox.mapbox-terrain-dem-v1',
      tileSize: 512,
      maxzoom: 14
    });

    this.mapInstance.setTerrain({ source: 'terrain', exaggeration: 1.5 });

    // 添加3D建筑
    this.mapInstance.addLayer({
      id: '3d-buildings',
      source: 'composite',
      'source-layer': 'building',
      filter: ['==', 'extrude', 'true'],
      type: 'fill-extrusion',
      minzoom: 15,
      paint: {
        'fill-extrusion-color': '#aaa',
        'fill-extrusion-height': [
          'interpolate',
          ['linear'],
          ['zoom'],
          15, 0,
          15.05, ['get', 'height']
        ],
        'fill-extrusion-base': [
          'interpolate',
          ['linear'],
          ['zoom'],
          15, 0,
          15.05, ['get', 'min_height']
        ],
        'fill-extrusion-opacity': 0.6
      }
    });

    // 添加3D水体模拟
    if (data.floodSimulation) {
      this.addFloodSimulation(data.floodSimulation);
    }
  }

  private addFloodSimulation(floodData: FloodSimulationData) {
    const layerId = 'flood-simulation';

    this.mapInstance.addLayer({
      id: layerId,
      type: 'fill-extrusion',
      source: {
        type: 'geojson',
        data: floodData.inundatedAreas
      },
      paint: {
        'fill-extrusion-color': '#4FC3F7',
        'fill-extrusion-height': [
          'interpolate',
          ['linear'],
          ['get', 'water_depth'],
          0, 0,
          5, 5
        ],
        'fill-extrusion-opacity': 0.8,
        'fill-extrusion-vertical-gradient': false
      }
    });

    // 添加水体动画
    this.animateWaterFlow(layerId, floodData.flowData);
  }

  private animateWaterFlow(layerId: string, flowData: FlowData) {
    this.animationEngine.startAnimation(`water-flow-${layerId}`, {
      duration: 10000,
      update: (progress: number) => {
        // 更新水流方向和速度
        const updatedFlow = this.updateFlowDirection(flowData, progress);
        this.mapInstance.getSource(`${layerId}-flow`)?.setData(updatedFlow);
      }
    });
  }
}

// React组件封装
const InteractiveSituationMapComponent: React.FC<SituationMapProps> = ({
  data,
  config,
  onMapClick,
  onFeatureClick,
  onAnalysisComplete
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<InteractiveSituationMap | null>(null);

  useEffect(() => {
    if (!mapContainer.current) return;

    // 初始化地图
    mapInstance.current = new InteractiveSituationMap(mapContainer.current, config);

    // 绑定事件
    mapInstance.current.on('click', onMapClick);
    mapInstance.current.on('feature-click', onFeatureClick);

    return () => {
      mapInstance.current?.destroy();
    };
  }, [config, onMapClick, onFeatureClick]);

  useEffect(() => {
    if (!mapInstance.current || !data) return;

    // 清除现有图层
    mapInstance.current.clearLayers();

    // 添加数据图层
    data.situationAnalysis && mapInstance.current.addSituationAnalysisLayer(data.situationAnalysis);
    data.resources && mapInstance.current.addResourceLayer(data.resources);
    data.realTimeData && mapInstance.current.animateRealTimeData(data.realTimeData);

    onAnalysisComplete?.();
  }, [data, onAnalysisComplete]);

  return (
    <div className="interactive-situation-map">
      <div ref={mapContainer} className="map-container" />
      <div className="map-controls">
        <MapTools map={mapInstance.current} />
      </div>
    </div>
  );
};
```

### 7.3 移动端支持

#### 7.3.1 响应式设计优化
**优先级**: P1 (高)

**功能描述**:
- 完整的移动端响应式设计
- 触摸友好的交互界面
- 优化的性能和加载速度
- 离线模式支持

**设计方案**:
```scss
// 移动端响应式设计
.safe-embedded-components {
  // 基础断点
  $mobile-breakpoint: 768px;
  $tablet-breakpoint: 1024px;
  $desktop-breakpoint: 1200px;

  // 移动端优化
  @media (max-width: $mobile-breakpoint) {
    .smart-analysis-card {
      &--small {
        .safe-analysis-card__header {
          padding: 8px 12px;
          font-size: 14px;
        }

        .safe-analysis-card__body {
          padding: 12px;
        }

        .safe-analysis-card__metrics {
          grid-template-columns: 1fr;
          gap: 8px;
        }
      }

      &--medium {
        .safe-analysis-card__header {
          flex-direction: column;
          align-items: flex-start;
          gap: 8px;
        }

        .safe-analysis-card__meta {
          width: 100%;
          justify-content: space-between;
        }
      }
    }

    .decision-recommendation {
      &.recommendation-modal {
        .ant-modal {
          margin: 0;
          max-width: 100vw;
          height: 100vh;
        }

        .ant-modal-content {
          height: 100vh;
          border-radius: 0;
        }
      }

      .recommendation-card {
        margin-bottom: 16px;
      }

      .recommendation-steps {
        .ant-steps {
          .ant-steps-item {
            .ant-steps-item-content {
              min-height: auto;
            }
          }
        }
      }
    }

    .agent-status-indicator {
      &--horizontal {
        flex-direction: column;
        gap: 12px;
      }

      .agent-indicator {
        &--medium {
          .agent-indicator__basic {
            flex-direction: column;
            gap: 8px;
          }

          .agent-indicator__metrics {
            .agent-metrics {
              display: grid;
              grid-template-columns: repeat(3, 1fr);
              gap: 4px;
            }
          }
        }
      }
    }
  }

  // 平板端优化
  @media (min-width: $mobile-breakpoint) and (max-width: $tablet-breakpoint) {
    .smart-analysis-card {
      &--large {
        .safe-analysis-card__metrics {
          grid-template-columns: repeat(2, 1fr);
        }
      }
    }

    .interactive-situation-map {
      .map-container {
        height: 500px;
      }

      .map-controls {
        bottom: 20px;
        right: 20px;
      }
    }
  }

  // 触摸优化
  @media (hover: none) and (pointer: coarse) {
    .safe-analysis-card {
      &.safe-analysis-card--interactive {
        min-height: 44px; // 最小触摸目标
        padding: 12px;
      }

      .safe-analysis-card__actions {
        .ant-btn {
          min-height: 44px;
          min-width: 44px;
          padding: 8px 16px;
        }
      }
    }

    .decision-recommendation {
      .recommendation-actions {
        .ant-btn {
          min-height: 44px;
          margin: 4px;
        }
      }
    }

    .agent-status-indicator {
      .agent-indicator {
        &.agent-indicator--clickable {
          min-height: 44px;
          padding: 12px;
        }
      }
    }
  }
}

// 移动端专用组件
.mobile-optimized-interface {
  // 底部操作栏
  .mobile-action-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: white;
    border-top: 1px solid #e8e8e8;
    padding: 12px 16px;
    z-index: 1000;

    .action-buttons {
      display: flex;
      gap: 12px;
      justify-content: space-around;

      .action-btn {
        flex: 1;
        min-height: 44px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        border: none;
        background: transparent;
        color: #666;
        font-size: 12px;

        .icon {
          font-size: 20px;
        }

        &.active {
          color: #1890ff;
        }
      }
    }
  }

  // 滑动面板
  .mobile-slide-panel {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: white;
    border-radius: 16px 16px 0 0;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
    z-index: 1001;
    transform: translateY(100%);
    transition: transform 0.3s ease;

    &.open {
      transform: translateY(0);
    }

    .panel-header {
      padding: 16px;
      border-bottom: 1px solid #f0f0f0;
      display: flex;
      align-items: center;
      justify-content: space-between;

      .panel-title {
        font-size: 16px;
        font-weight: 600;
      }

      .close-btn {
        width: 32px;
        height: 32px;
        border: none;
        background: transparent;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;

        &:hover {
          background: #f5f5f5;
        }
      }
    }

    .panel-content {
      padding: 16px;
      max-height: 70vh;
      overflow-y: auto;
    }

    .panel-handle {
      position: absolute;
      top: 8px;
      left: 50%;
      transform: translateX(-50%);
      width: 40px;
      height: 4px;
      background: #d9d9d9;
      border-radius: 2px;
    }
  }
}
```

#### 7.3.2 移动端性能优化
**优先级**: P2 (中)

**功能描述**:
- 针对移动端的性能优化
- 懒加载和代码分割
- 图片和资源优化
- 缓存策略优化

**优化策略**:
```typescript
// 移动端性能优化工具
class MobilePerformanceOptimizer {
  private lazyLoader: LazyLoader;
  private resourceOptimizer: ResourceOptimizer;
  private cacheManager: CacheManager;

  constructor() {
    this.initializeOptimizations();
  }

  private initializeOptimizations() {
    // 检测设备类型
    const isMobile = this.detectMobileDevice();
    const isLowEndDevice = this.detectLowEndDevice();

    if (isMobile) {
      this.enableMobileOptimizations();
    }

    if (isLowEndDevice) {
      this.enableLowEndOptimizations();
    }
  }

  // 懒加载实现
  setupLazyLoading() {
    this.lazyLoader = new LazyLoader({
      rootMargin: '50px',
      threshold: 0.1,
      load: (element: Element) => {
        if (element instanceof HTMLImageElement) {
          this.loadImageOptimized(element);
        } else if (element instanceof HTMLElement) {
          this.loadComponentOptimized(element);
        }
      }
    });

    // 观察所有需要懒加载的元素
    document.querySelectorAll('[data-lazy]').forEach(element => {
      this.lazyLoader.observe(element);
    });
  }

  // 图片优化加载
  private async loadImageOptimized(img: HTMLImageElement) {
    const src = img.dataset.src;
    if (!src) return;

    // 检测设备像素比
    const dpr = window.devicePixelRatio || 1;

    // 根据网络状况选择合适的图片质量
    const connection = (navigator as any).connection;
    const quality = this.getOptimalImageQuality(connection);

    // 构建优化的图片URL
    const optimizedSrc = this.buildOptimizedImageUrl(src, {
      width: img.offsetWidth * dpr,
      quality: quality,
      format: this.getOptimalFormat()
    });

    // 预加载图片
    const tempImg = new Image();
    tempImg.onload = () => {
      img.src = optimizedSrc;
      img.classList.add('loaded');
    };
    tempImg.onerror = () => {
      // 降级处理
      img.src = src;
    };
    tempImg.src = optimizedSrc;
  }

  // 组件懒加载
  private async loadComponentOptimized(element: HTMLElement) {
    const componentName = element.dataset.component;
    if (!componentName) return;

    try {
      // 动态导入组件
      const module = await import(`../components/${componentName}`);
      const Component = module.default;

      // 创建并挂载组件
      const componentElement = document.createElement(componentName);
      element.parentNode?.replaceChild(componentElement, element);

    } catch (error) {
      console.error(`加载组件 ${componentName} 失败:`, error);
      element.innerHTML = '<div class="load-error">组件加载失败</div>';
    }
  }

  // 缓存管理
  setupCacheManagement() {
    this.cacheManager = new CacheManager({
      storage: 'localStorage', // 或 'indexedDB'
      maxSize: 50 * 1024 * 1024, // 50MB
      defaultTTL: 24 * 60 * 60 * 1000 // 24小时
    });

    // 缓存API响应
    this.setupAPICaching();

    // 缓存静态资源
    this.setupResourceCaching();
  }

  private setupAPICaching() {
    // 拦截fetch请求
    const originalFetch = window.fetch;
    window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString();

      // 只缓存GET请求
      if (init?.method !== 'GET' && init?.method !== undefined) {
        return originalFetch(input, init);
      }

      // 检查缓存
      const cachedResponse = await this.cacheManager.get(url);
      if (cachedResponse) {
        return new Response(cachedResponse.data, {
          status: cachedResponse.status,
          statusText: cachedResponse.statusText,
          headers: new Headers(cachedResponse.headers)
        });
      }

      // 发起请求
      const response = await originalFetch(input, init);

      // 缓存响应（仅缓存成功的响应）
      if (response.ok) {
        const responseData = await response.clone().text();
        await this.cacheManager.set(url, {
          data: responseData,
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries())
        });
      }

      return response;
    };
  }

  // 网络状态监听
  setupNetworkMonitoring() {
    const connection = (navigator as any).connection;

    if (connection) {
      connection.addEventListener('change', () => {
        this.adaptToNetworkConditions(connection);
      });

      // 初始适配
      this.adaptToNetworkConditions(connection);
    }
  }

  private adaptToNetworkConditions(connection: any) {
    const { effectiveType, downlink } = connection;

    // 根据网络状况调整策略
    if (effectiveType === 'slow-2g' || effectiveType === '2g') {
      this.enableUltraLowBandwidthMode();
    } else if (effectiveType === '3g') {
      this.enableLowBandwidthMode();
    } else {
      this.enableNormalMode();
    }
  }

  private enableUltraLowBandwidthMode() {
    // 禁用动画
    document.body.classList.add('reduce-motion');

    // 降低图片质量
    document.querySelectorAll('img').forEach(img => {
      img.style.imageRendering = 'auto';
    });

    // 禁用自动刷新
    this.disableAutoRefresh();

    // 启用压缩
    this.enableDataCompression();
  }

  // 触摸优化
  setupTouchOptimizations() {
    // 防抖动处理
    let touchStartTime: number;
    let touchStartX: number;
    let touchStartY: number;

    document.addEventListener('touchstart', (e) => {
      touchStartTime = Date.now();
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    });

    document.addEventListener('touchend', (e) => {
      const touchEndTime = Date.now();
      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;

      // 检测是否为点击（而非滑动）
      const timeDiff = touchEndTime - touchStartTime;
      const distanceDiff = Math.sqrt(
        Math.pow(touchEndX - touchStartX, 2) +
        Math.pow(touchEndY - touchStartY, 2)
      );

      if (timeDiff < 200 && distanceDiff < 10) {
        // 触发点击事件
        const target = e.target as HTMLElement;
        target.click();
      }
    });

    // 添加触摸反馈
    document.addEventListener('touchstart', (e) => {
      const target = e.target as HTMLElement;
      target.classList.add('touch-active');
    });

    document.addEventListener('touchend', (e) => {
      const target = e.target as HTMLElement;
      setTimeout(() => {
        target.classList.remove('touch-active');
      }, 150);
    });
  }
}

// PWA支持
class PWASupport {
  private deferredPrompt: any = null;

  constructor() {
    this.registerServiceWorker();
    this.setupInstallPrompt();
  }

  private async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker 注册成功:', registration);

        // 监听更新
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // 显示更新提示
                this.showUpdatePrompt();
              }
            });
          }
        });

      } catch (error) {
        console.error('Service Worker 注册失败:', error);
      }
    }
  }

  private setupInstallPrompt() {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
      this.showInstallButton();
    });
  }

  private showInstallButton() {
    const installBtn = document.createElement('button');
    installBtn.textContent = '安装应用';
    installBtn.className = 'pwa-install-btn';
    installBtn.addEventListener('click', async () => {
      if (this.deferredPrompt) {
        this.deferredPrompt.prompt();
        const { outcome } = await this.deferredPrompt.userChoice;
        console.log(`用户选择: ${outcome}`);
        this.deferredPrompt = null;
        installBtn.remove();
      }
    });

    document.body.appendChild(installBtn);
  }

  private showUpdatePrompt() {
    const updateModal = document.createElement('div');
    updateModal.className = 'update-modal';
    updateModal.innerHTML = `
      <div class="update-content">
        <h3>应用更新可用</h3>
        <p>新版本已准备就绪，是否立即更新？</p>
        <div class="update-actions">
          <button id="update-now">立即更新</button>
          <button id="update-later">稍后更新</button>
        </div>
      </div>
    `;

    document.body.appendChild(updateModal);

    document.getElementById('update-now')?.addEventListener('click', () => {
      window.location.reload();
    });

    document.getElementById('update-later')?.addEventListener('click', () => {
      updateModal.remove();
    });
  }
}
```

## 实施计划

### Phase 1: 嵌入式组件开发 (第1-3周)
**目标**: 开发核心嵌入式组件库

**主要任务**:
1. 设计组件架构和接口规范
2. 开发智能分析卡片组件
3. 实现决策建议浮窗组件
4. 构建Agent状态指示器
5. 开发快速操作面板组件

**交付物**:
- 嵌入式组件库
- 组件API文档
- 使用示例和教程
- 单元测试覆盖

**验收标准**:
- 组件功能完整且稳定
- API接口清晰易用
- 文档详细准确
- 测试覆盖率 ≥ 80%

### Phase 2: 高级可视化功能 (第4-5周)
**目标**: 实现高级数据可视化功能

**主要任务**:
1. 开发交互式态势地图
2. 实现3D可视化功能
3. 构建高级图表组件
4. 开发数据探索工具
5. 实现动画和过渡效果

**交付物**:
- 交互式地图组件
- 3D可视化模块
- 高级图表库
- 数据探索工具

**验收标准**:
- 可视化效果流畅美观
- 交互响应及时
- 支持大数据量渲染
- 兼容主流浏览器

### Phase 3: 移动端适配 (第6-7周)
**目标**: 完成移动端适配和优化

**主要任务**:
1. 实现响应式设计
2. 优化移动端交互
3. 开发移动端专用功能
4. 实现离线模式支持
5. 性能优化和测试

**交付物**:
- 响应式设计系统
- 移动端优化版本
- 离线功能模块
- 性能优化报告

**验收标准**:
- 移动端体验良好
- 性能指标达标
- 离线功能可用
- 兼容主流移动设备

### Phase 4: 集成适配和测试 (第8-9周)
**目标**: 完成系统集成适配和全面测试

**主要任务**:
1. 开发SIMAP集成适配器
2. 实现主题样式适配
3. 进行跨浏览器测试
4. 性能压力测试
5. 用户体验测试

**交付物**:
- 集成适配器
- 主题样式系统
- 测试报告
- 性能基准

**验收标准**:
- 集成功能正常
- 兼容性良好
- 性能达标
- 用户满意度高

### Phase 5: 文档和培训 (第10周)
**目标**: 完成文档编写和培训准备

**主要任务**:
1. 编写技术文档
2. 制作使用教程
3. 准备培训材料
4. 录制演示视频
5. 准备发布版本

**交付物**:
- 完整技术文档
- 使用教程
- 培训材料
- 演示视频

**验收标准**:
- 文档完整准确
- 教程易懂实用
- 培训材料充分
- 发布版本稳定

## 风险与缓解措施

### 技术风险

#### 1. 组件兼容性问题
**风险等级**: 中等
**影响**: 组件在某些环境中无法正常工作
**缓解措施**:
- 建立完善的兼容性测试
- 提供Polyfill和降级方案
- 支持多种集成方式
- 建立快速响应机制

#### 2. 性能优化挑战
**风险等级**: 中等
**影响**: 移动端和低配设备性能不佳
**缓解措施**:
- 采用渐进式增强策略
- 实现智能加载和缓存
- 建立性能监控体系
- 提供多种性能配置

#### 3. 移动端适配复杂度高
**风险等级**: 中等
**影响**: 移动端体验不佳，兼容性问题
**缓解措施**:
- 采用响应式设计框架
- 进行充分的移动端测试
- 提供移动端专用组件
- 建立设备适配策略

### 业务风险

#### 1. 用户接受度问题
**风险等级**: 中等
**影响**: 嵌入式组件使用率不高
**缓解措施**:
- 加强用户需求调研
- 提供平滑的集成体验
- 建立用户反馈机制
- 持续优化用户体验

#### 2. 维护成本增加
**风险等级**: 低
**影响**: 多平台维护成本上升
**缓解措施**:
- 建立自动化测试体系
- 采用组件化开发模式
- 建立统一的代码规范
- 实现持续集成部署

## 验收标准

### 功能验收

#### 嵌入式组件
- [ ] 智能分析卡片功能完整
- [ ] 决策建议浮窗交互良好
- [ ] Agent状态指示器准确及时
- [ ] 快速操作面板便捷高效

#### 高级功能
- [ ] 交互式地图功能丰富
- [ ] 3D可视化效果良好
- [ ] 高级图表展示准确
- [ ] 数据探索工具实用

#### 移动端支持
- [ ] 响应式设计适配良好
- [ ] 移动端交互流畅
- [ ] 离线模式功能可用
- [ ] 性能优化效果明显

### 性能验收

#### 加载性能
- [ ] 组件加载时间 ≤ 2秒
- [ ] 地图渲染时间 ≤ 3秒
- [ ] 移动端首屏时间 ≤ 4秒
- [ ] 3D渲染帧率 ≥ 30fps

#### 运行性能
- [ ] 组件响应时间 ≤ 200ms
- [ ] 内存占用 ≤ 100MB
- [ ] CPU占用率 ≤ 30%
- [ ] 电池消耗优化

### 质量验收

#### 兼容性
- [ ] 支持Chrome 90+
- [ ] 支持Safari 14+
- [ ] 支持Firefox 88+
- [ ] 支持Edge 90+

#### 用户体验
- [ ] 界面设计美观一致
- [ ] 交互操作直观易用
- [ ] 错误提示友好明确
- [ ] 用户满意度 ≥ 4.5/5.0

## 后续规划

### Epic 8衔接准备
- 为性能优化提供组件级基准
- 支持更大规模的部署和应用
- 建立组件生态和扩展机制

### 长期规划
- 建立开放的组件生态系统
- 支持第三方插件开发
- 提供云端组件服务
- 实现跨平台组件复用

---

**文档版本**: v1.0
**创建日期**: 2025-10-19
**作者**: John (产品经理)
**审批状态**: 待审批
**下次更新**: 根据开发进展更新