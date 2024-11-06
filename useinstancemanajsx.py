import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import useFetch from '@/components/usefetch'

export const useInstanceManagement = (user) => {
  const [instances, setInstances] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionInProgress, setActionInProgress] = useState({})
  const [resumeButtonText, setResumeButtonText] = useState('')
  const [isErrorModalOpen, setIsErrorModalOpen] = useState(false)
  const [isPauseModalOpen, setIsPauseModalOpen] = useState(false)
  const [errorModalContent, setErrorModalContent] = useState({})
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [isH100, setIsH100] = useState(false)
  const [isVM, setIsVM] = useState(false)
  const [selectedInstanceId, setSelectedInstanceId] = useState(null)
  const { authenticatedFetch: fetchInstancesAPI } = useFetch()
  const { authenticatedFetch: deleteInstancesAPI } = useFetch()
  const { authenticatedFetch: postData } = useFetch()
  const { authenticatedFetch: getResumeStatus } = useFetch()
  const { authenticatedFetch: editInstName } = useFetch()

  const timerRefs = useRef({})
  const size =
    instances.vSize && instances.vSize > 0 ? instances.vSize.toFixed(2) : 0
  const sizeStr = size > 0 ? `${size} /` : ''

  const instanceGpuType = useMemo(() => {
    if (instances.framework === 'upgrad') {
      return instances.gpuType === 'CPU' ? 'CPU' : 'GPU'
    }
    return instances.gpuType === 'A5000Pro' ? 'A5000' : instances.gpuType
  }, [instances.framework, instances.gpuType])

  const router = useRouter()

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true)
      try {
        await fetchInstances()
      } catch (err) {
        console.error('Error fetching instances:', err)
        setError('Failed to load instances. Please try again later.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchData() // Initial fetch

    const fetchInstancesInterval = setInterval(fetchInstances, 3 * 60 * 1000) // Set up interval
    return () => {
      clearInterval(fetchInstancesInterval) // Cleanup interval on unmount
    }
  }, [])

  useEffect(() => {
    instances.forEach((instance) => {
      setActionInProgress((prev) => ({
        ...prev,
        [instance.id]: {
          action: instance.status,
          originalStatus: prev[instance.id]?.originalStatus,
        },
      }))
      const shouldPoll = ![
        'Running',
        'Stopped',
        'Paused',
        'Failed',
        'Resumed',
        'Resuming',
      ].includes(instance.status)
      if (shouldPoll) {
        handleResumeStatus(instance.id)

        if (timerRefs.current[instance.id]) {
          clearInterval(timerRefs.current[instance.id])
        }

        timerRefs.current[instance.id] = setInterval(() => {
          handleResumeStatus(instance.id)
        }, 500)
      }
    })
    return () => {
      Object.values(timerRefs.current).forEach(clearInterval)
    }
  }, [instances])

  const pauseModalContent = {
    heading: 'Storage Costs Apply for Paused Instances',
    subheading:
      'Please be aware that pausing your instance will incur storage charges at $0.00014 per hour/GB',
  }
  const openPauseModal = (instance_id, instance) => {
    if (instances.framework === 'upgrad') {
      handlePauseInstance(instance_id)
    } else {
      setSelectedInstanceId(instance_id)
      setIsH100(instance.gpuType == 'H100' && instance.framework == 'pytorch')
      setIsVM(instance.framework == 'vm')
      setIsPauseModalOpen(true)
    }
  }
  const closePauseModal = () => {
    setIsPauseModalOpen(false)
  }
  const onPauseButtonClick = (instance_id) => {
    setSelectedInstanceId(instance_id)
    handlePauseInstance(selectedInstanceId, isH100, isVM)
    closePauseModal()
  }

  const confirmInstanceDeletion = useCallback((instanceId, isH100, isVM) => {
    setSelectedInstanceId(instanceId)
    setIsDeleteModalOpen(true)
    setIsH100(isH100)
    setIsVM(isVM)
  }, [])

  const closeDeleteModal = useCallback(() => {
    setIsDeleteModalOpen(false)
    setSelectedInstanceId(null)
  }, [])

  const onDeleteButtonClick = useCallback(async () => {
    closeDeleteModal()
    await handleDestroyInstance(selectedInstanceId, isH100, isVM)
  }, [selectedInstanceId, closeDeleteModal])

  const isTeamInstance = useCallback(
    (instance) => {
      return user && instance.userID !== user.emailAddresses[0]?.emailAddress
    },
    [user],
  )

  const fetchInstances = async () => {
    const controller = new AbortController()
    const signal = controller.signal
    const url = process.env.NEXT_PUBLIC_API_URL + 'users/fetch'

    try {
      const response = await fetchInstancesAPI(url, 'GET', null, false, signal)
      if (response.error) {
        console.error('Error fetching instances:', response.error)
      } else {
        const instancesArr = response.data.instances.map((value) => ({
          id: value['machine_id'],
          name: value['instance_name'],
          status: value['status'],
          originalStatus: value['status'],
          hdd: value['hdd'],
          cost: value['cost'],
          duration: value['duration'],
          gpuType: value['gpu_type'],
          ram: value['ram'],
          cores: value['cores'],
          numGpus: value['num_gpus'],
          url: value['url'],
          version: value['version'],
          framework: value['framework'],
          sshStr: value['ssh_str'],
          vSize: value['v_size'],
          APIEndpointUrls: value['endpoints'],
          frameworkID: value['framework_id'],
          frequency: value['frequency'],
          isReserved: Boolean(value['is_reserved']),
          vsUrl: value['vs_url'],
          userID: value['user_id'],
          diskType: value['disk_type'],
        }))
        setInstances(instancesArr)
        setIsLoading(false)
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Fetch aborted')
      } else {
        console.error('Unhandled error fetching instances', error)
      }
    }
  }

  const handleResumeInstance = useCallback(async (instanceId, instance) => {
    try {
      const controller = new AbortController()
      const { signal } = controller

      setActionInProgress((prev) => ({
        ...prev,
        [instanceId]: { action: 'Resuming', originalStatus: instance.status },
      }))

      let framework = instance.framework ? instance.framework.toLowerCase() : ''

      const data = { machine_id: instanceId.toString() }

      const backendAPI =
        instance.framework == 'pytorch' && instance.gpuType == 'H100'
          ? process.env.NEXT_PUBLIC_TEMPLATES_API_URL
          : process.env.NEXT_PUBLIC_API_URL

      const url = `${backendAPI}templates/${framework}/resume`
      const response = await postData(url, 'POST', data, false, signal)

      if (response.error) {
        console.error('Error resuming instance:', response.error)
        setActionInProgress((prev) => ({ ...prev, [instanceId]: null }))
      } else if (response.status === 200) {
        handleResumeStatus(response.data.machine_id)
        const timer = setInterval(
          () => {
            handleResumeStatus(response.data.machine_id, timer)
          },
          isH100 ? 3000 : 500,
        )
      } else {
        setActionInProgress((prev) => ({ ...prev, [instanceId]: null }))
        let heading = 'Oh, resuming your instance failed!'
        const subheading = response.data.message
        if (subheading?.includes('storage')) heading = 'Low Storage Alert!'
        const content = {
          heading,
          subheading,
        }
        setIsErrorModalOpen(true)
        setCancelModalContent(content)
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Fetch aborted')
      } else {
        console.error('Unhandled error in resuming instance:', error)
        setActionInProgress((prev) => ({ ...prev, [instanceId]: false }))
      }
    }
  }, [])

  const handleResumeStatus = useCallback(async (id, timer) => {
    try {
      const controller = new AbortController()
      const { signal } = controller
      const url = `${process.env.NEXT_PUBLIC_API_URL}misc/status?machine_id=${encodeURIComponent(id)}`

      const response = await getResumeStatus(url, 'GET', null, false, signal)

      if (response.error) {
        console.error('Error getting status:', response.error)
        setIsErrorModalOpen(true)

        const content = {
          heading: 'Resuming your instance failed',
          subheading: response.error,
        }
        setErrorModalContent(content)
      } else if (response.data) {
        setActionInProgress((prev) => ({
          ...prev,
          [id]: {
            action: response.data.status,
            originalStatus: prev[id]?.originalStatus,
          },
        }))

        if (response.data.status === 'Failed') {
          setIsErrorModalOpen(true)

          const content = {
            heading: 'Resuming Instance failed',
            subheading: response.data.error,
          }
          setErrorModalContent(content)
          clearInterval(timer)
          fetchInstances()
        }

        if (
          response.data.status === 'Running' ||
          response.data.status === 'Stopped'
        ) {
          fetchInstances()
          clearInterval(timer)
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Fetch aborted')
      } else {
        console.error('Unhandled error in getting resuming status:', error)
      }
    }
  }, [])

  const handleDestroyInstance = async (machineId, isH100, isVM) => {
    const backendAPI = isH100
      ? process.env.NEXT_PUBLIC_TEMPLATES_API_URL
      : process.env.NEXT_PUBLIC_API_URL

    const url = `${backendAPI}${isVM ? 'templates/vm' : 'misc'}/destroy?machine_id=${encodeURIComponent(machineId)}`

    const instance = instances.find((i) => i.id === machineId)
    const originalStatus = instance ? instance.status : 'Unknown'
    setActionInProgress((prev) => ({
      ...prev,
      [machineId]: { action: 'Deleting', originalStatus: 'Deleting' },
    }))

    try {
      const response = await deleteInstancesAPI(url, 'POST', null, false)

      if (response.error) {
        console.error('Error destroying instance:', response.error)
        setIsErrorModalOpen(true)
        const content = {
          heading: 'Destroying  your instance failed',
          subheading: response.error,
        }
        setErrorModalContent(content)
      } else if (response.status === 200) {
        fetchInstances()
      }
    } catch (error) {
      console.error('Unhandled error in deletion instance:', error)
    } finally {
      setActionInProgress((prev) => {
        const newState = { ...prev }
        delete newState[machineId]
        return newState
      })
      await fetchInstances()
    }
  }

  const handlePauseInstance = async (instanceId, isH100, isVM) => {
    setActionInProgress((prev) => ({
      ...prev,
      [instanceId]: {
        action: 'Pausing',
        originalStatus: instances.find((i) => i.id === instanceId).status,
      },
    }))
    const url = isH100
      ? `${process.env.NEXT_PUBLIC_TEMPLATES_API_URL}misc/pause?machine_id=${encodeURIComponent(instanceId)}`
      : `${process.env.NEXT_PUBLIC_API_URL}${isVM ? 'templates/vm' : 'misc'}/pause?machine_id=${encodeURIComponent(instanceId)}`
    try {
      const response = await postData(url, 'POST', null, false)

      if (response.error) {
        throw new Error(response.error)
      } else if (response.status === 200) {
        setInstances((prevInstances) =>
          prevInstances.map((inst) =>
            inst.id === instanceId
              ? { ...inst, status: 'Paused', originalStatus: 'Paused' }
              : inst,
          ),
        )
      } else {
        setErrorModalContent({
          heading: 'Pausing your instance failed!',
          subheading: 'Please try again later.',
        })
        setIsErrorModalOpen(true)
        fetchInstances()
        throw new Error('Pausing your instance failed!')
      }
    } catch (error) {
      console.error('Error pausing instance:', error)
    }
    fetchInstances()
    setActionInProgress((prev) => ({ ...prev, [instanceId]: false }))
  }

  const handleEditInstance = useCallback(
    (instance) => {
      if (!instance || !instance.framework) {
        console.error('Instance or framework is undefined.')
        return
      }

      const frameworkName = instance.framework.startsWith('u_')
        ? 'upgrad'
        : instance.framework

      let url = `/templates/${frameworkName}`
      if (frameworkName == 'vm') url = `/${frameworkName}/create`
      console.log(instance.hdd)

      const queryParams = [
        `machineid=${instance.id}`,
        `storage=${instance.hdd}`,
        `gpuQty=${instance.numGpus}`,
        `instancename=${instance.name}`,
        `gpuType=${instance.gpuType}`,
        `frequency=${instance.frequency}`,
        `reserved=${instance.isReserved}`,
      ]

      if (instance.framework == 'vm') {
        queryParams.push(`diskType=${instance.diskType}`)
      }

      url += `?${queryParams.join('&')}`
      router.push(url)
    },
    [router],
  )

const EditableInstanceName = ({ instance, onSave }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(instance.name);
  const inputRef = useRef(null);

  const handleSaveClick = () => {
    const regexPattern = /^(?=.{1,30}$).*$/; // Regex for name validation

    if (name.trim() === '') {
      setName(instance.framework); // Revert to default name
      alert('Instance name cannot be empty. Reverting to default.');
    } else if (!regexPattern.test(name)) {
      alert('Instance name should be 1-30 characters long.');
      inputRef.current.focus(); // Focus on input if validation fails
    } else {
      onSave(instance.id, name); // Save if valid
      setIsEditing(false);
    }
  };

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.select(); // Automatically select the text when editing starts
    }
  }, [isEditing]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSaveClick();
    }
  };

  return (
    <div className="flex items-center">
      {isEditing ? (
        <input
          type="text"
          ref={inputRef}
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={handleSaveClick} // Save on blur
          onKeyDown={handleKeyDown} // Save on Enter key press
          className="border border-black rounded px-2 py-1 text-sm bg-transparent text-white"
          style={{ outline: 'none', color: 'white' }}
        />
      ) : (
        <span
          onClick={() => setIsEditing(true)} // Click to edit
          className="text-white cursor-pointer relative group"
        >
          {name}
          <span className="absolute left-1/2 transform -translate-x-1/2 top-[-1.5rem] bg-gray-700 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            Click to edit
          </span>
        </span>
      )}
    </div>
  );
};

const handleSaveInstanceName = async (id, newName) => {
  const url = `${process.env.NEXT_PUBLIC_API_URL}machines/machine_name?machine_id=${encodeURIComponent(id)}&machine_name=${encodeURIComponent(newName)}`;

  try {
    const response = await editInstName(url, 'PUT', null, false);

    if (response.error) {
      console.error('Error updating instance name:', response.error);
      throw new Error(response.error);
    } else if (response.status === 200) {
      console.log('Instance name updated successfully:', response.data);
      return true;
    }
  } catch (error) {
    console.error('Failed to update instance name:', error);
    throw error;
  }
}; 
  return {
    instances,
    isLoading,
    error,
    actionInProgress,
    resumeButtonText,
    isErrorModalOpen,
    errorModalContent,
    isDeleteModalOpen,
    isPauseModalOpen,
    selectedInstanceId,
    pauseModalContent,
    closePauseModal,
    openPauseModal,
    onPauseButtonClick,
    setActionInProgress,
    setSelectedInstanceId,
    isTeamInstance,
    fetchInstances,
    handleResumeInstance,
    confirmInstanceDeletion,
    closeDeleteModal,
    onDeleteButtonClick,
    handlePauseInstance,
    handleEditInstance,
    setIsErrorModalOpen,
    EditableInstanceName,
    handleSaveInstanceName,
  }
}
