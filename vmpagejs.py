'use client'
import React from 'react'
import Link from 'next/link'
import { useInstanceManagement } from '@/hooks/useInstanceManagement'
import Table from '@/components/Table'
import { useBalanceFrameworksContext } from '@/components/BalanceFrameworksContext'
import { SSHButton } from '@/components/SSHButton'
import DeleteModal from '@/components/deleteModal'
import CancelModal from '@/components/CancelModal'
import PauseModal from '@/components/pauseModal'
import PageHeader from '@/components/PageHeader'
import CopyButton from '@/components/CopyButton'
import NoVm from '@/components/NoVm'
import { Loader, Edit, Trash2, Pause, Play, Plus } from 'lucide-react'
const deleteModalContent = {
  heading: 'Are you sure you want to delete this Instance',
  subheading:
    'Caution: Deleting your instance! Your valuable data and model weights will vanish. Once you delete your account, there is no going back. Please be certain.',
}

const VMPage = () => {
  const {
    instances,
    isLoading,
    error,
    actionInProgress,
    isErrorModalOpen,
    errorModalContent,
    isDeleteModalOpen,
    isPauseModalOpen,
    selectedInstanceId,
    pauseModalContent,
    isVM,
    openPauseModal,
    onPauseButtonClick,
    isSelectedGPUH100,
    closePauseModal,
    isTeamInstance,
    handleResumeInstance,
    confirmInstanceDeletion,
    closeDeleteModal,
    onDeleteButtonClick,
    handlePauseInstance,
    handleEditInstance,
    setIsErrorModalOpen,
     EditableInstanceName,
    handleSaveInstanceName,
  } = useInstanceManagement()

  const { isINR } = useBalanceFrameworksContext()
  const vmInstances = instances.filter(
    (instance) => instance.framework === 'vm',
  )

  const vmColumns = [
    { key: 'name', label: ' Name' },
    { key: 'status', label: 'Status' },
    { key: 'cost', label: 'Cost' },
    { key: 'control', label: 'Access' },
    { key: 'actions', label: 'Actions' },
  ]
  const getExpandedInstanceContent = (instance) => {
    const baseContent = [
      { key: 'gpu_details', label: 'GPU' },
      { key: 'machine_id', label: 'Machine ID' },
      { key: 'hdd', label: 'Storage' },
      { key: 'duration', label: 'Duration' },
    ]
    if (instance.status === 'Running' && instance.gpuType !== 'H100') {
      baseContent.push({ key: 'viewLogs', label: 'ViewLogs' })
    }
    if (isTeamInstance(instance))
      baseContent.push({ key: 'team', label: 'Team' })

    return baseContent
  }
  const InstanceStatus = ({ instance, actionInProgress }) => {
    const action = actionInProgress[instance.id]
    const displayStatus = action ? action.action : instance.status
    const statusClass =
      displayStatus === 'Running'
        ? 'bg-green-100 text-green-800'
        : displayStatus === 'Paused'
          ? 'bg-yellow-100 text-yellow-800'
          : displayStatus === 'Stopped'
            ? 'bg-red-100 text-red-800'
            : 'bg-blue-100 text-blue-800'

    return (
      <div className="flex items-center space-x-2">
        <span
          className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${statusClass}`}
        >
          {displayStatus}
        </span>
      </div>
    )
  }

  const renderActionButtons = (instance) => {
    const isDisabled =
      !['Running', 'Paused'].includes(instance.status) &&
      actionInProgress[instance.id]?.action !== 'Running'

    const isActionInProgress = [
      'Pausing',
      'Resuming',
      'Deleting',
      'Destroying',
    ].includes(actionInProgress[instance.id]?.action)

    const buttonClass = `${isDisabled || isActionInProgress ? 'opacity-20 cursor-not-allowed' : ''}`
    return (
      <div className="flex space-x-2">
        {instance.status === 'Paused' && (
          <>
            <button
              onClick={() => handleResumeInstance(instance.id, instance)}
              className={` flex items-center gap-x-1 rounded bg-gray-600 px-2 py-1 text-xs text-white hover:bg-gray-800 ${buttonClass}`}
              disabled={isDisabled || isActionInProgress}
            >
              <Play size={14} />
              Resume
            </button>

            <button
              onClick={() => handleEditInstance(instance)}
              className={`flex items-center gap-x-1 rounded bg-gray-600 px-2 py-1 text-xs text-white hover:bg-gray-800 ${buttonClass}`}
              disabled={isDisabled || isActionInProgress}
            >
              <Edit size={14} className="mr-1" />
              Edit
            </button>
          </>
        )}
        {instance.status === 'Running' && (
          <button
            onClick={() => openPauseModal(instance.id, instance)}
            className={`flex items-center gap-x-1 rounded bg-gray-600 px-2 py-1 text-xs text-white hover:bg-gray-800 ${buttonClass}`}
            disabled={isDisabled || isActionInProgress}
          >
            <Pause size={14} className="mr-1" />
            Pause
          </button>
        )}

        <button
          onClick={() => confirmInstanceDeletion(instance.id, false, true)}
          className={`flex items-center gap-x-1 rounded bg-gray-600 px-2 py-1 text-xs text-white hover:bg-gray-800 ${buttonClass}`}
          disabled={isDisabled || isActionInProgress}
        >
          <Trash2 size={16} className="mr-1" />
          Delete
        </button>
      </div>
    )
  }

  const transformInstanceData = (instances) => {
    return instances
      .filter(
        (instance) =>
          instance.status !== 'Resumed' && instance.status !== 'Resuming',
      )
      .map((instance) => ({
        id: instance.machine_id,
        name: (
      <EditableInstanceName
        instance={instance}
        onSave={(id, newName) => {
          // Calling handleSaveInstanceName when saving a new instance name
          handleSaveInstanceName(id, newName);
        }}
      />
    ),
        status: (
          <InstanceStatus
            instance={instance}
            actionInProgress={actionInProgress}
          />
        ),
        cost: `${isINR ? '₹' : '$'}  ${instance.cost.toFixed(2)}`,
        control: renderControlButtons(instance),
        actions: renderActionButtons(instance),
        gpu_details: `${instance.numGpus} x ${instance.gpuType}`,
        framework: instance.framework,
        machine_id: renderMachineId(instance.id),
        hdd: `${instance.hdd} GB`,
        duration: instance.duration || '-',
        expandedContent: getExpandedInstanceContent(instance),
      }))
  }

  const renderMachineId = (MachineID) => {
    return (
      <div className="flex flex-wrap">
        <span>{MachineID}</span>
        <CopyButton textToCopy={MachineID} />
      </div>
    )
  }
  const isDisabledStatus = (status) => {
    return status === 'serverallocated' || status === 'deleting'
  }

  const renderControlButtons = (instance) => {
    const isDisabled = instance.status !== 'Running'
    const buttonClass = `z-20 flex items-center rounded bg-gray-700 px-2 py-1 text-xs text-gray-300 hover:bg-gray-600   ${isDisabled ? 'opacity-20 cursor-not-allowed' : ''} `

    return (
      <div className="flex flex-wrap gap-2">
        <SSHButton instance={instance} buttonClass={buttonClass} />
      </div>
    )
  }

  const VMInstancesTable = ({ instances }) => (
    <div>
      <PageHeader
        title="Your Virtual Machines"
        buttonText="Create VM"
        buttonLink="/vm/create"
      />

      <Table
        data={transformInstanceData(instances)}
        columns={vmColumns}
        expandedContent={(instance) => instance.expandedContent}
        renderControlButtons={renderControlButtons}
        isRowDisabled={(instance) => isDisabledStatus(instance.status)}
      />
    </div>
  )

  if (isLoading)
    return (
      <div className="flex h-screen w-screen  items-center justify-center">
        <Loader className="h-8 w-8 animate-spin text-indigo-500" />
        <span className="ml-2 text-gray-300">Loading ..</span>
      </div>
    )
  if (error)
    return (
      <div className="my-20 text-center  text-red-500 ">Error: {error}</div>
    )
  return (
    <div className="vm-page-container">
      {vmInstances.length > 0 ? (
        <VMInstancesTable instances={vmInstances} />
      ) : (
        <NoVm />
      )}

      {isPauseModalOpen && (
        <PauseModal
          onPause={() => onPauseButtonClick()}
          onCancel={closePauseModal}
          modalContent={pauseModalContent}
          isInstance={true}
          isVM={isVM}
          isSelectedGPUH100={isSelectedGPUH100}
          diskType={instances.diskType}
        />
      )}

      {isDeleteModalOpen && (
        <DeleteModal
          onDelete={onDeleteButtonClick}
          onCancel={closeDeleteModal}
          modalContent={deleteModalContent}
          isInstance={true}
        />
      )}

      {isErrorModalOpen && (
        <CancelModal
          onCancel={() => setIsErrorModalOpen(false)}
          cancelMessage={errorModalContent}
        />
      )}
    </div>
  )
}
export default VMPage
