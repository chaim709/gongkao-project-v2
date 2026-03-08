import { useState } from 'react';
import { Tag, Button, Modal, Form, Select, InputNumber, Space, Popconfirm, message, Empty } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { weaknessApi } from '../../api/weakness';
import type { WeaknessTag, WeaknessTagCreate, ModuleCategory } from '../../api/weakness';

const levelColorMap: Record<string, string> = {
  red: 'red',
  yellow: 'orange',
  green: 'green',
};

const levelTextMap: Record<string, string> = {
  red: '薄弱',
  yellow: '一般',
  green: '掌握',
};

interface Props {
  studentId: number;
}

export default function WeaknessTagPanel({ studentId }: Props) {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const { data: tags = [], isLoading } = useQuery({
    queryKey: ['weaknesses', studentId],
    queryFn: () => weaknessApi.getStudentWeaknesses(studentId),
  });

  const { data: modules = [] } = useQuery({
    queryKey: ['modules'],
    queryFn: () => weaknessApi.getModules(),
  });

  const createMutation = useMutation({
    mutationFn: (data: WeaknessTagCreate) => weaknessApi.createWeakness(studentId, data),
    onSuccess: () => {
      message.success('添加成功');
      queryClient.invalidateQueries({ queryKey: ['weaknesses', studentId] });
      setModalOpen(false);
      form.resetFields();
    },
    onError: () => message.error('添加失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: weaknessApi.deleteWeakness,
    onSuccess: () => {
      message.success('删除成功');
      queryClient.invalidateQueries({ queryKey: ['weaknesses', studentId] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<WeaknessTagCreate> }) =>
      weaknessApi.updateWeakness(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weaknesses', studentId] });
    },
  });

  // 获取一级模块选项（去重）
  const level1Options = [...new Set(modules.map((m: ModuleCategory) => m.level1))].map(v => ({
    label: v, value: v,
  }));

  // 根据选中的一级模块获取二级选项
  const selectedLevel1 = Form.useWatch('module_name', form);
  const level2Options = modules
    .filter((m: ModuleCategory) => m.level1 === selectedLevel1 && m.level2)
    .map((m: ModuleCategory) => ({ label: m.level2!, value: m.level2!, moduleId: m.id }));

  const handleSubmit = () => {
    form.validateFields().then((values) => {
      const matchedModule = modules.find(
        (m: ModuleCategory) => m.level1 === values.module_name && m.level2 === values.sub_module_name
      );
      createMutation.mutate({
        ...values,
        module_id: matchedModule?.id,
      });
    });
  };

  const cycleLevel = (tag: WeaknessTag) => {
    const order = ['green', 'yellow', 'red'];
    const nextIdx = (order.indexOf(tag.level) + 1) % order.length;
    updateMutation.mutate({ id: tag.id, data: { level: order[nextIdx] } });
  };

  if (isLoading) return null;

  return (
    <div>
      <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong>薄弱项标签</strong>
        <Button size="small" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>添加</Button>
      </div>

      {tags.length === 0 ? (
        <Empty description="暂无薄弱项标签" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <Space size={[4, 8]} wrap>
          {tags.map((tag: WeaknessTag) => (
            <Tag
              key={tag.id}
              color={levelColorMap[tag.level]}
              style={{ cursor: 'pointer', marginBottom: 4 }}
              onClick={() => cycleLevel(tag)}
            >
              {tag.module_name}
              {tag.sub_module_name ? ` / ${tag.sub_module_name}` : ''}
              {tag.accuracy_rate != null ? ` ${tag.accuracy_rate}%` : ''}
              <span style={{ marginLeft: 4, fontSize: 10 }}>({levelTextMap[tag.level]})</span>
              <Popconfirm title="确认删除？" onConfirm={(e) => { e?.stopPropagation(); deleteMutation.mutate(tag.id); }}>
                <DeleteOutlined style={{ marginLeft: 6, fontSize: 10 }} onClick={(e) => e.stopPropagation()} />
              </Popconfirm>
            </Tag>
          ))}
        </Space>
      )}

      <Modal
        title="添加薄弱项"
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields(); }}
        onOk={handleSubmit}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" initialValues={{ level: 'yellow', practice_count: 0 }}>
          <Form.Item name="module_name" label="知识模块" rules={[{ required: true, message: '请选择知识模块' }]}>
            <Select options={level1Options} placeholder="选择一级模块" />
          </Form.Item>
          <Form.Item name="sub_module_name" label="具体知识点">
            <Select options={level2Options} placeholder="选择二级知识点" allowClear />
          </Form.Item>
          <Form.Item name="level" label="掌握程度" rules={[{ required: true }]}>
            <Select options={[
              { label: '薄弱（红色）', value: 'red' },
              { label: '一般（黄色）', value: 'yellow' },
              { label: '掌握（绿色）', value: 'green' },
            ]} />
          </Form.Item>
          <Form.Item name="accuracy_rate" label="正确率（%）">
            <InputNumber min={0} max={100} precision={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="practice_count" label="练习次数">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
