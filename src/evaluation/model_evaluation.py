import numpy as np

def calculate_rmse(array1, array2):
    """
    Calculate the Root Mean Square Error (RMSE) between two NumPy arrays.

    Parameters:
    array1 (numpy.ndarray): First array.
    array2 (numpy.ndarray): Second array.

    Returns:
    float: The RMSE value.
    """
    # Ensure that the input arrays are NumPy arrays
    array1 = np.array(array1)
    array2 = np.array(array2)

    # Check if the arrays have the same shape
    if array1.shape != array2.shape:
        raise ValueError("The input arrays must have the same shape.")

    # Calculate the Mean Squared Error (MSE)
    mse = np.mean((array1 - array2) ** 2)

    # Calculate the Root Mean Square Error (RMSE)
    rmse = np.sqrt(mse)

    return rmse

def calculate_mae(array1, array2):
    """
    Calculate the Mean Absolute Error (MAE) between two NumPy arrays.

    Parameters:
    array1 (numpy.ndarray): First array.
    array2 (numpy.ndarray): Second array.

    Returns:
    float: The MAE value.
    """
    # Ensure that the input arrays are NumPy arrays
    array1 = np.array(array1)
    array2 = np.array(array2)

    # Check if the arrays have the same shape
    if array1.shape != array2.shape:
        raise ValueError("The input arrays must have the same shape.")

    # Calculate the Mean Absolute Error (MAE)
    mae = np.mean(np.abs(array1 - array2))

    return mae

