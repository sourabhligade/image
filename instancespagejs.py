'use client'
import React, { useState ,useRef, useEffect} from 'react'
import Image from 'next/image'
import Table from '@/components/Table'
import { ViewLogs } from '@/components/ViewLogs'
import { SSHButton } from '@/components/SSHButton'
import CopyButton from '@/components/CopyButton'

import APIEndpointsModal from '@/components/APIEndpointsModal'
import { useBalanceFrameworksContext } from '@/components/BalanceFrameworksContext'
import { Play, Loader, Edit, Trash2, Pause, Eye } from 'lucide-react'
import { useUser } from '@clerk/nextjs'
import NoInstances from '@/components/NoInstances'
import DeleteModal from '@/components/deleteModal'
import CancelModal from '@/components/CancelModal'
import PauseModal from '@/components/pauseModal'
import { useInstanceManagement } from '@/hooks/useInstanceManagement'
import PageHeader from '@/components/PageHeader'
import useFetch from '@/components/usefetch'

const url_tools = 'https://jarvislabs.net/jarvislabs_website/button_logos/'

const deleteModalContent = {
  heading: 'Are you sure you want to delete this Instance',
  subheading:
    'Caution: Deleting your instance! Your valuable data and model weights will vanish. Once you delete your account, there is no going back. Please be certain.',
}

export default function Instances() {
  const { user } = useUser()
  const { isINR } = useBalanceFrameworksContext()
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
  } = useInstanceManagement(user)


  const nonVMInstances = instances?.filter(
    (instance) => instance.framework !== 'vm',
  )
  const isDisabledStatus = (status) => {
    return status === 'server allocated' || status === 'deleting'
  }
  const renderActionButtons = (instance) => {
    const isDisabled =
      !['Running', 'Pausing', 'Deleting', 'Paused'].includes(instance.status) &&
      actionInProgress[instance.id]?.action !== 'Running'

    const isActionInProgress = ['Pausing', 'Resuming', 'Deleting'].includes(
      actionInProgress[instance.id]?.action,
    )

    const buttonClass = `${isDisabled || isActionInProgress ? 'opacity-20 cursor-not-allowed' : ''}`
    return (
      <div className="flex space-x-2">
        {instance.status === 'Paused' && (
          <>
            <button
              onClick={() =>
                instance.framework === 'autotrain'
                  ? handleEditInstance(instance)
                  : handleResumeInstance(instance.id, instance)
              }
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
          onClick={() =>
            confirmInstanceDeletion(
              instance.id,
              instance.framework == 'pytorch' && instance.gpuType == 'H100',
              false,
            )
          }
          className={`flex items-center gap-x-1 rounded bg-gray-600 px-2 py-1 text-xs text-white hover:bg-gray-800 ${buttonClass}`}
          disabled={isDisabled || isActionInProgress}
        >
          <Trash2 size={16} className="mr-1" />
          Delete
        </button>
      </div>
    )
  }
  const renderControlButtons = (instance) => {
    const isDisabled =
      instance.status !== 'Running' ||
      actionInProgress[instance.id]?.action !== 'Running'

    const buttonClass = ` z-20 flex items-center rounded bg-gray-700 px-2 py-1 text-xs text-gray-300 hover:bg-gray-600   ${isDisabled ? 'opacity-20 cursor-not-allowed' : ''} `

    return (
      <div className="flex flex-wrap gap-2">
        <a
          href={isDisabled ? '#' : `${instance.url}`}
          className={buttonClass}
          target="_blank"
          onClick={(e) => isDisabled && e.preventDefault()}
        >
          <Image
            quality={75}
            src={url_tools + 'jupyter.avif'}
            height={28}
            width={24}
            className="mr-1 h-4 w-4"
            alt="Jupyter"
          />
          <span className="hidden sm:inline">Jupyter</span>
        </a>
        <a
          href={isDisabled ? '#' : instance.vsUrl}
          className={buttonClass}
          target="_blank"
          onClick={(e) => isDisabled && e.preventDefault()}
        >
          <Image
            quality={75}
            src={url_tools + 'vscode.svg'}
            height={28}
            width={24}
            className="mr-1 h-4 w-5"
            alt="VSCode"
          />
          <span className="hidden sm:inline">VS Code</span>
        </a>
        <SSHButton instance={instance} buttonClass={buttonClass} />

        <APIEndpointsModal
          apiUrls={instance.APIEndpointUrls}
          isDisabled={isDisabled}
          buttonClass={buttonClass}
        ></APIEndpointsModal>
      </div>
    )
  }

if (isLoading) {
    return (
      <div className="my-20 flex justify-center">
        <Loader className="h-8 w-8 animate-spin text-indigo-500" />
        <span className="ml-2 text-gray-300">Loading instances...</span>
      </div>
    )
  }
  if (error) {
    return <div className="text-center text-red-500">{error}</div>
  }
  if (isLoading || !nonVMInstances || nonVMInstances.length === 0) {
    return <NoInstances />
  }
  const instanceColumns = [
    { key: 'name', label: 'Name' },
    { key: 'status', label: 'Status' },
    { key: 'cost', label: 'Cost' },
    { key: 'control', label: 'Access' },
    { key: 'actions', label: 'Actions' },
  ]
  const getExpandedInstanceContent = (instance) => {
    const baseContent = [
      { key: 'framework', label: 'Framework' },
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
  const ViewLogsButton = ({ instanceId, framework, status }) => {
    if (status !== 'Running') return null

    const [isLogsModalOpen, setIsLogsModalOpen] = useState(false)

    const handleClick = () => {
      setIsLogsModalOpen(true)
    }

    return (
      <>
        <button
          onClick={handleClick}
          className="flex items-center gap-x-1 rounded bg-gray-600 px-2 py-1 text-xs text-white hover:bg-gray-800"
        >
          <Eye size={14} className="mr-1" />
          View Logs
        </button>

        {isLogsModalOpen && (
          <ViewLogs
            machineId={instanceId}
            setIsLogsModalOpen={setIsLogsModalOpen}
            isLogsModalOpen={isLogsModalOpen}
            framework={framework}
            onClose={() => {
              setIsLogsModalOpen(false)
            }}
          />
        )}
      </>
    )
  }
  const transformInstanceData = (instances) => {
    return instances
      .filter(
        (instance) =>
          instance.status !== 'Resumed' &&
          instance.status !== 'Resuming' &&
          instance.framework !== 'vm',
      )
      .map((instance) => ({
        id: instance.id,
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
        cost: ` ${isINR ? '₹' : '$'}  ${instance.cost.toFixed(2)}`,
        control: renderControlButtons(instance),
        actions: renderActionButtons(instance),
        framework: instance.framework,
        viewLogs: (
          <ViewLogsButton
            status={instance.status}
            instanceId={instance.id}
            framework={instance.framework}
          />
        ),
        gpu_details: `${instance.numGpus} x ${instance.gpuType}`,
        machine_id: (
          <div className="flex items-center">
            <span className="max-w-[100px] truncate sm:max-w-[150px]">
              {instance.id}
            </span>
            <CopyButton textToCopy={instance.id} />
          </div>
        ),
        hdd: `${instance.hdd} GB`,
        team: isTeamInstance(instance) ? instance.userID : '-',
        duration: instance.duration || '-',
        expandedContent: getExpandedInstanceContent(instance),
      }))
  }

  return (
    <div>
      <PageHeader
        title="Your Instances"
        buttonText="Create Instance"
        buttonLink="/explore?filter=templates"
      />
      <Table
        data={transformInstanceData(instances)}
        columns={instanceColumns}
        expandedContent={(instance) => instance.expandedContent}
        renderControlButtons={renderControlButtons}
        isRowDisabled={(instance) => isDisabledStatus(instance.status)}
      />

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
